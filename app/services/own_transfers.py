import re
import uuid
from collections import Counter
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.transaction import Transaction, TransactionType
from app.models.user import User

TRANSFER_WORDS = {
    "transfer", "transferred", "transfers", "raast", "ibft", "p2p", "fund", "funds",
    "sent", "received", "incoming", "outgoing", "ft", "remittance",
}
NOT_TRANSFER_FLAG = "not_own_transfer"

MIN_NAME_KEY = 4
MAX_NAME_WORDS = 3
PAIR_WINDOW = timedelta(days=3)
NAMELESS_PAIR_WINDOW = timedelta(days=1)


def name_key(text: str) -> str:
    return re.sub(r"[aeiouy]", "", re.sub(r"[^a-z]", "", text.lower()))


def mentions_name(description: str, full_name: str) -> bool:
    key = name_key(full_name)

    if len(full_name.split()) < 2 or len(key) < MIN_NAME_KEY:
        return False

    words = re.findall(r"[a-z]+", description.lower())

    for size in range(1, MAX_NAME_WORDS + 1):
        for start in range(len(words) - size + 1):
            if name_key("".join(words[start:start + size])) == key:
                return True

    return False


def has_transfer_word(description: str) -> bool:
    return bool(set(re.findall(r"[a-z0-9]+", description.lower())) & TRANSFER_WORDS)


def is_own_transfer(description: str, full_name: str) -> bool:
    return has_transfer_word(description) and mentions_name(description, full_name)


def _is_match(expense: Transaction, income: Transaction, window: timedelta) -> bool:
    return (
        income.amount == expense.amount
        and income.account_id != expense.account_id
        and abs(income.transaction_date - expense.transaction_date) <= window
    )


def pair_legs(legs: list[Transaction], window: timedelta = PAIR_WINDOW) -> list[list[Transaction]]:
    expenses = sorted((t for t in legs if t.type == TransactionType.EXPENSE), key=lambda t: t.transaction_date)
    incomes = sorted((t for t in legs if t.type == TransactionType.INCOME), key=lambda t: t.transaction_date)
    used: set[int] = set()
    groups: list[list[Transaction]] = []

    for expense in expenses:
        match = next(
            (
                income for income in incomes
                if id(income) not in used and _is_match(expense, income, window)
            ),
            None,
        )

        if match is None:
            groups.append([expense])
        else:
            used.add(id(match))
            groups.append([expense, match])

    groups.extend([income] for income in incomes if id(income) not in used)
    return groups


def _open_imported_rows(db: Session, user_id: uuid.UUID) -> list[Transaction]:
    return [
        txn for txn in db.scalars(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.transfer_group_id.is_(None),
                Transaction.import_batch_id.is_not(None),
                Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE]),
            )
        )
        if not (txn.raw_data or {}).get(NOT_TRANSFER_FLAG)
    ]


def _single_legs(db: Session, user_id: uuid.UUID) -> list[Transaction]:
    single_groups = select(Transaction.transfer_group_id).where(
        Transaction.user_id == user_id,
        Transaction.transfer_group_id.is_not(None),
    ).group_by(Transaction.transfer_group_id).having(func.count() == 1)

    return list(
        db.scalars(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.import_batch_id.is_not(None),
                Transaction.transfer_group_id.in_(single_groups),
            )
        )
    )


def _group(legs: list[Transaction]) -> None:
    group_id = next((t.transfer_group_id for t in legs if t.transfer_group_id), None) or uuid.uuid4()

    for txn in legs:
        txn.transfer_group_id = group_id


def mark_own_transfers(db: Session, user_id: uuid.UUID) -> list[Transaction]:
    user = db.get(User, user_id)

    if user is None:
        return []

    open_rows = _open_imported_rows(db, user_id)
    full_name = user.full_name or ""
    named = [txn for txn in open_rows if is_own_transfer(txn.description, full_name)]
    named_ids = {id(txn) for txn in named}
    nameless = [
        txn for txn in open_rows
        if id(txn) not in named_ids and has_transfer_word(txn.description)
    ]

    if not named and not nameless:
        return []

    singles = _single_legs(db, user_id)
    marked: list[Transaction] = []

    for group in pair_legs(named + singles):
        _group(group)
        marked.extend(txn for txn in group if id(txn) in named_ids)

    nameless_ids = {id(txn) for txn in nameless}
    sizes = Counter(txn.transfer_group_id for txn in named + singles)
    leftover = [txn for txn in named + singles if sizes[txn.transfer_group_id] == 1]
    for group in pair_legs(nameless + leftover, NAMELESS_PAIR_WINDOW):
        new_rows = [txn for txn in group if id(txn) in nameless_ids]
        if len(group) == 2 and new_rows:
            _group(group)
            marked.extend(new_rows)

    db.commit()
    return marked


def mark_as_transfer(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> list[Transaction]:
    txn = db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id))

    if txn is None:
        raise NotFoundError("Transaction not found")

    if txn.transfer_group_id is not None:
        raise BadRequestError("This transaction is already a transfer")

    if txn.import_batch_id is None:
        raise BadRequestError("Only imported transactions can be marked. Use Transfer to record a move between accounts")

    if txn.type not in (TransactionType.INCOME, TransactionType.EXPENSE):
        raise BadRequestError("Only income or expense rows can be marked as transfers")

    wanted = TransactionType.INCOME if txn.type == TransactionType.EXPENSE else TransactionType.EXPENSE
    candidates = [
        other for other in _open_imported_rows(db, user_id) + _single_legs(db, user_id)
        if other.id != txn.id and other.type == wanted
        and (
            _is_match(txn, other, PAIR_WINDOW) if txn.type == TransactionType.EXPENSE
            else _is_match(other, txn, PAIR_WINDOW)
        )
    ]
    partner = min(
        candidates,
        key=lambda other: (abs(other.transaction_date - txn.transaction_date), other.transfer_group_id is None),
        default=None,
    )
    legs = [txn] if partner is None else [txn, partner]
    _group(legs)

    for leg in legs:
        if (leg.raw_data or {}).get(NOT_TRANSFER_FLAG):
            leg.raw_data = {key: value for key, value in leg.raw_data.items() if key != NOT_TRANSFER_FLAG}

    db.commit()
    return legs


def unmark_transfer(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> list[Transaction]:
    txn = db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id))

    if txn is None:
        raise NotFoundError("Transaction not found")

    if txn.transfer_group_id is None:
        raise BadRequestError("This transaction is not a transfer")

    legs = list(
        db.scalars(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.transfer_group_id == txn.transfer_group_id,
            )
        )
    )

    if any(leg.import_batch_id is None for leg in legs):
        raise BadRequestError("This transfer was made in the app. Delete it instead")

    for leg in legs:
        leg.transfer_group_id = None
        leg.raw_data = {**(leg.raw_data or {}), NOT_TRANSFER_FLAG: True}

    db.commit()
    return legs
