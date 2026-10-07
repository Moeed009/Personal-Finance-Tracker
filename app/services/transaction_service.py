import uuid
from decimal import Decimal

from sqlalchemy import Select, case, delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.money import money
from app.models.transaction import TransactionType
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilters,
    TransactionSummary,
    TransactionUpdate,
    TransferCreate,
)
from app.services import account_service, category_service
from app.services.categorization import CategoryResolver, derive_merchant

MANUAL_TYPES = (TransactionType.INCOME, TransactionType.EXPENSE)


def _require_manual_type(transaction_type: TransactionType) -> None:
    if transaction_type not in MANUAL_TYPES:
        raise BadRequestError("Type must be INCOME or EXPENSE. Use POST /transfers to move money between accounts")


def _get(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
    txn = db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id))
    if txn is None:
        raise NotFoundError("Transaction not found")
    return txn


def _apply_filters(query: Select, filters: TransactionFilters) -> Select:
    if filters.account_id:
        query = query.where(Transaction.account_id == filters.account_id)
    if filters.category_id:
        query = query.where(Transaction.category_id == filters.category_id)
    if filters.type:
        query = query.where(Transaction.type == filters.type)
    if filters.date_from:
        query = query.where(Transaction.transaction_date >= filters.date_from)
    if filters.date_to:
        query = query.where(Transaction.transaction_date <= filters.date_to)
    if filters.min_amount is not None:
        query = query.where(Transaction.amount >= filters.min_amount)
    if filters.max_amount is not None:
        query = query.where(Transaction.amount <= filters.max_amount)
    if filters.search:
        query = query.where(
            or_(
                Transaction.description.icontains(filters.search, autoescape=True),
                Transaction.merchant.icontains(filters.search, autoescape=True),
            )
        )
    return query


def create_transaction(db: Session, user_id: uuid.UUID, data: TransactionCreate) -> Transaction:
    _require_manual_type(data.type)
    account_service.get_account(db, user_id, data.account_id)
    if data.category_id:
        category_service.ensure_compatible(category_service.get_category(db, user_id, data.category_id), data.type)
        category_id = data.category_id
    else:
        category_id = CategoryResolver(db, user_id).resolve(data.description, data.type)
    txn = Transaction(
        user_id=user_id,
        account_id=data.account_id,
        category_id=category_id,
        type=data.type,
        amount=data.amount,
        description=data.description.strip(),
        merchant=(data.merchant or derive_merchant(data.description) or "").strip().lower() or None,
        transaction_date=data.transaction_date,
    )
    db.add(txn)
    db.commit()
    return txn


def list_transactions(db: Session, user_id: uuid.UUID, filters: TransactionFilters) -> tuple[list[Transaction], int]:
    query = _apply_filters(select(Transaction).where(Transaction.user_id == user_id), filters)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(
        query.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    ).all()
    return list(items), total


def get_summary(db: Session, user_id: uuid.UUID, filters: TransactionFilters) -> TransactionSummary:
    expense = case((Transaction.type == TransactionType.EXPENSE, Transaction.amount), else_=0)
    income = case((Transaction.type == TransactionType.INCOME, Transaction.amount), else_=0)
    query = _apply_filters(
        select(func.coalesce(func.sum(expense), 0), func.coalesce(func.sum(income), 0)).where(
            Transaction.user_id == user_id
        ),
        filters,
    )
    total_debit, total_credit = db.execute(query).one()
    if filters.account_id:
        accounts = [account_service.get_account_with_balance(db, user_id, filters.account_id)]
        balance = accounts[0].balance
    else:
        accounts, balance = account_service.summary(db, user_id)
    opening_balance = money(sum((account.opening_balance for account in accounts), Decimal("0")))
    return TransactionSummary(
        opening_balance=opening_balance,
        total_debit=money(total_debit),
        total_credit=money(total_credit),
        balance=balance,
    )


def update_transaction(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID, data: TransactionUpdate) -> Transaction:
    txn = _get(db, user_id, transaction_id)
    if txn.transfer_group_id:
        raise BadRequestError("Transfer transactions cannot be edited. Delete the transfer and create a new one")
    changes = data.model_dump(exclude_unset=True)
    if "type" in changes and changes["type"] is not None:
        _require_manual_type(changes["type"])
    if changes.get("account_id"):
        account_service.get_account(db, user_id, changes["account_id"])
    for field in ("account_id", "type", "amount", "transaction_date", "description"):
        if changes.get(field) is not None:
            setattr(txn, field, changes[field])
    if "merchant" in changes:
        txn.merchant = (changes["merchant"] or derive_merchant(txn.description) or "").strip().lower() or None
    elif "description" in changes and changes["description"] is not None:
        txn.merchant = derive_merchant(txn.description)
    if "category_id" in changes:
        if changes["category_id"] is None:
            txn.category_id = CategoryResolver(db, user_id).uncategorized_id
        else:
            category_service.ensure_compatible(
                category_service.get_category(db, user_id, changes["category_id"]), txn.type
            )
            txn.category_id = changes["category_id"]
    elif txn.category_id:
        current = category_service.get_category(db, user_id, txn.category_id)
        try:
            category_service.ensure_compatible(current, txn.type)
        except BadRequestError:
            txn.category_id = CategoryResolver(db, user_id).resolve(txn.description, txn.type)
    db.commit()
    return txn


def delete_transaction(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
    txn = _get(db, user_id, transaction_id)
    if txn.transfer_group_id:
        db.execute(
            delete(Transaction).where(
                Transaction.transfer_group_id == txn.transfer_group_id, Transaction.user_id == user_id
            )
        )
    else:
        db.delete(txn)
    db.commit()


def create_transfer(db: Session, user_id: uuid.UUID, data: TransferCreate) -> tuple[uuid.UUID, Transaction, Transaction]:
    if data.from_account_id == data.to_account_id:
        raise BadRequestError("Source and destination accounts must be different")
    source = account_service.get_account(db, user_id, data.from_account_id)
    target = account_service.get_account(db, user_id, data.to_account_id)
    group_id = uuid.uuid4()
    common = {"user_id": user_id, "amount": data.amount, "transaction_date": data.transaction_date,
              "transfer_group_id": group_id}
    outgoing = Transaction(account_id=source.id, type=TransactionType.EXPENSE,
                           description=f"{data.description} to {target.name}"[:300], **common)
    incoming = Transaction(account_id=target.id, type=TransactionType.INCOME,
                           description=f"{data.description} from {source.name}"[:300], **common)
    db.add_all([outgoing, incoming])
    db.commit()
    return group_id, outgoing, incoming