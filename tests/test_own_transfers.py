import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.models.transaction import TransactionType
from app.services.own_transfers import is_own_transfer, name_key, pair_legs

NAME = "Abdul Moeed"


def test_name_key_ignores_vowels_case_and_spaces():
    assert name_key("Abdul Moeed") == name_key("ABDUL MUEED") == name_key("Abdulmoeed")


@pytest.mark.parametrize(
    "description",
    [
        "Outgoing fund transfer to Abdul Moeed OPay-1551",
        "Incoming fund transfer from Abdul Mueed JazzCash/Mobilink MFB-1551",
        "Incoming fund transfer from Abdulmoeed JSBL-1128",
        "Raast P2P Fund transfer to Abdul Moeed PK46NAYAxxxx1128",
        "Money Transferred to ABDUL MUEED Jazz Cash STAN(647419)",
        "Bank Transfer NAYA | 03216171128 | Abdul Moeed",
    ],
)
def test_own_transfers_are_recognised(description):
    assert is_own_transfer(description, NAME)


@pytest.mark.parametrize(
    "description",
    [
        "Incoming fund transfer from Tahira Nasreen JazzCash/Mobilink MFB-3857",
        "Raast P2P Fund transfer - - from NAZIA RIAZ RAAST PYxxxx1090",
        "Outgoing fund transfer to Abdul Majid",
        "Abdul Moeed salary",
        "Paid to KFC - GULSHAN-E-RAVI LAHORE PK",
        "Cash Withdrawn at ATM",
    ],
)
def test_other_rows_are_not_own_transfers(description):
    assert not is_own_transfer(description, NAME)


def test_a_single_word_name_never_matches():
    assert not is_own_transfer("Outgoing fund transfer to Moeed", "Moeed")


def _leg(kind, amount, account, day):
    return SimpleNamespace(
        type=kind, amount=Decimal(amount), account_id=account, transaction_date=date(2026, 10, day), transfer_group_id=None
    )


def test_both_sides_of_a_move_are_paired():
    meezan, nayapay = uuid.uuid4(), uuid.uuid4()
    out = _leg(TransactionType.EXPENSE, "3300", meezan, 9)
    into = _leg(TransactionType.INCOME, "3300", nayapay, 10)
    same_account = _leg(TransactionType.INCOME, "6000", meezan, 7)
    other_amount = _leg(TransactionType.EXPENSE, "6000.50", nayapay, 7)

    groups = pair_legs([out, into, same_account, other_amount])

    assert [out, into] in groups
    assert [same_account] in groups
    assert [other_amount] in groups
