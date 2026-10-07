import uuid
from decimal import Decimal

from sqlalchemy import ColumnElement, and_, case, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import storage
from app.core.exceptions import ConflictError, NotFoundError
from app.core.money import money
from app.models.account import Account
from app.models.import_batch import ImportBatch
from app.models.recurring import RecurringExpense
from app.models.transaction import Transaction, TransactionType
from app.schemas.account import AccountBalanceSummary, AccountCreate, AccountUpdate


def compute_balances(db: Session, user_id: uuid.UUID) -> dict[uuid.UUID, Decimal]:
    signed = case(
        (Transaction.type == TransactionType.INCOME, Transaction.amount),
        (Transaction.type == TransactionType.EXPENSE, -Transaction.amount),
        else_=0,
    )
    flows = dict(
        db.execute(
            select(Transaction.account_id, func.coalesce(func.sum(signed), 0))
            .where(Transaction.user_id == user_id)
            .group_by(Transaction.account_id)
        ).all()
    )
    accounts = db.execute(select(Account.id, Account.opening_balance).where(Account.user_id == user_id)).all()
    return {
        account_id: money(opening) + money(flows.get(account_id, 0)) for account_id, opening in accounts
    }


def _with_balance(account: Account, balance: Decimal) -> Account:
    account.balance = balance
    return account


def list_accounts(db: Session, user_id: uuid.UUID) -> list[Account]:
    balances = compute_balances(db, user_id)
    accounts = db.scalars(select(Account).where(Account.user_id == user_id).order_by(Account.created_at, Account.name))
    return [_with_balance(a, balances[a.id]) for a in accounts]


def summary(db: Session, user_id: uuid.UUID) -> tuple[list[Account], Decimal]:
    accounts = list_accounts(db, user_id)
    return accounts, money(sum((a.balance for a in accounts), Decimal("0")))


def get_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    account = db.scalar(select(Account).where(Account.id == account_id, Account.user_id == user_id))
    if account is None:
        raise NotFoundError("Account not found")
    return account


def get_account_with_balance(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    account = get_account(db, user_id, account_id)
    return _with_balance(account, compute_balances(db, user_id)[account.id])


def get_account_summary(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> AccountBalanceSummary:
    account = get_account(db, user_id, account_id)
    regular = Transaction.transfer_group_id.is_(None)
    transfer = Transaction.transfer_group_id.is_not(None)

    def total(transaction_type: TransactionType, scope: ColumnElement[bool]) -> ColumnElement[Decimal]:
        return func.coalesce(
            func.sum(case((and_(Transaction.type == transaction_type, scope), Transaction.amount), else_=0)), 0
        )

    income, expense, transfer_in, transfer_out, count, last_date = db.execute(
        select(
            total(TransactionType.INCOME, regular),
            total(TransactionType.EXPENSE, regular),
            total(TransactionType.INCOME, transfer),
            total(TransactionType.EXPENSE, transfer),
            func.count(Transaction.id),
            func.max(Transaction.transaction_date),
        ).where(Transaction.account_id == account.id, Transaction.user_id == user_id)
    ).one()

    opening = money(account.opening_balance)
    income, expense = money(income), money(expense)
    transfer_in, transfer_out = money(transfer_in), money(transfer_out)
    return AccountBalanceSummary(
        account_id=account.id,
        account_name=account.name,
        account_type=account.type,
        opening_balance=opening,
        current_balance=opening + income + transfer_in - expense - transfer_out,
        total_income=income,
        total_expense=expense,
        transfer_in=transfer_in,
        transfer_out=transfer_out,
        transaction_count=count,
        last_transaction_date=last_date,
    )


def _ensure_name_free(db: Session, user_id: uuid.UUID, name: str, exclude_id: uuid.UUID | None = None) -> None:
    query = select(Account.id).where(Account.user_id == user_id, func.lower(Account.name) == name.lower())
    if exclude_id:
        query = query.where(Account.id != exclude_id)
    if db.scalar(query) is not None:
        raise ConflictError("You already have an account with this name")


def create_account(db: Session, user_id: uuid.UUID, data: AccountCreate) -> Account:
    name = data.name.strip()
    _ensure_name_free(db, user_id, name)
    account = Account(user_id=user_id, name=name, type=data.type, opening_balance=data.opening_balance)
    db.add(account)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("You already have an account with this name")
    return _with_balance(account, money(data.opening_balance))


def update_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID, data: AccountUpdate) -> Account:
    account = get_account(db, user_id, account_id)
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes and changes["name"] is not None:
        changes["name"] = changes["name"].strip()
        _ensure_name_free(db, user_id, changes["name"], exclude_id=account.id)
    for field, value in changes.items():
        if value is not None:
            setattr(account, field, value)
    db.commit()
    return _with_balance(account, compute_balances(db, user_id)[account.id])


def delete_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID, force: bool = False) -> None:
    account = get_account(db, user_id, account_id)
    has_transactions = db.scalar(
        select(func.count()).select_from(Transaction).where(Transaction.account_id == account.id)
    )
    if has_transactions and not force:
        raise ConflictError("Account has transactions. Use force=true to delete the account and all its transactions")
    paths = list(db.scalars(select(ImportBatch.storage_path).where(ImportBatch.account_id == account.id)))
    db.execute(delete(Transaction).where(Transaction.account_id == account.id))
    db.execute(delete(RecurringExpense).where(RecurringExpense.account_id == account.id))
    db.execute(delete(ImportBatch).where(ImportBatch.account_id == account.id))
    db.execute(delete(Account).where(Account.id == account.id))
    db.commit()
    storage.remove_files(paths)