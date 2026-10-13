"""Recognise money moved between the user's own accounts.

Bank statements show a move from Meezan to NayaPay as an expense in one
statement and as income in the other. Counted as spending and earning it
distorts every total, so these rows are marked as transfers: they get a
transfer_group_id, which keeps them out of income, expenses, budgets and
reports while account balances stay correct.

A row counts as an own transfer when its description has a transfer word
("transfer", "Raast", "IBFT", ...) and the user's own name. Names are
compared without vowels or spaces, so "Abdul Moeed", "ABDUL MUEED" and
"Abdulmoeed" all match. When both sides of a move are imported (an
expense in one account and income of the same amount in another, within a
few days) they share one transfer group, like a transfer made in the app.
"""

import re
import uuid
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
MIN_NAME_KEY = 4
MAX_NAME_WORDS = 3
PAIR_WINDOW = timedelta(days=3)


def name_key(text: str) -> str:
    """Letters only, without vowels: 'Abdul Moeed' and 'Abdul Mueed' -> 'bdlmd'."""
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


def is_own_transfer(description: str, full_name: str) -> bool:
    words = set(re.findall(r"[a-z0-9]+", description.lower()))
    return bool(words & TRANSFER_WORDS) and mentions_name(description, full_name)


def pair_legs(legs: list[Transaction]) -> list[list[Transaction]]:
    """Group legs into transfers: an expense and an income of the same amount
    in different accounts within PAIR_WINDOW. Unmatched legs stand alone."""
    expenses = sorted((t for t in legs if t.type == TransactionType.EXPENSE), key=lambda t: t.transaction_date)
    incomes = sorted((t for t in legs if t.type == TransactionType.INCOME), key=lambda t: t.transaction_date)
    used: set[int] = set()
    groups: list[list[Transaction]] = []

    for expense in expenses:
        match = next(
            (
                income for income in incomes
                if id(income) not in used
                and income.amount == expense.amount
                and income.account_id != expense.account_id
                and abs(income.transaction_date - expense.transaction_date) <= PAIR_WINDOW
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


def mark_own_transfers(db: Session, user_id: uuid.UUID) -> int:
    """Mark the user's own transfers among imported rows; return how many rows were marked."""
    user = db.get(User, user_id)

    if user is None or not user.full_name:
        return 0

    candidates = [
        txn for txn in db.scalars(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.transfer_group_id.is_(None),
                Transaction.import_batch_id.is_not(None),
                Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE]),
            )
        )
        if is_own_transfer(txn.description, user.full_name)
    ]

    if not candidates:
        return 0

    # Earlier imports may have left one side of a move unmatched; let the new
    # rows pair up with it.
    single_groups = select(Transaction.transfer_group_id).where(
        Transaction.user_id == user_id,
        Transaction.transfer_group_id.is_not(None),
    ).group_by(Transaction.transfer_group_id).having(func.count() == 1)

    singles = list(
        db.scalars(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.import_batch_id.is_not(None),
                Transaction.transfer_group_id.in_(single_groups),
            )
        )
    )

    for group in pair_legs(candidates + singles):
        group_id = next((t.transfer_group_id for t in group if t.transfer_group_id), None) or uuid.uuid4()

        for txn in group:
            txn.transfer_group_id = group_id

    db.commit()
    return len(candidates)


def unmark_transfer(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
    """Undo an automatic match: the rows count as income or expense again.

    Only transfers recognised from imported rows can be undone this way;
    a transfer made in the app is removed by deleting it.
    """
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

    db.commit()
