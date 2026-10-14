import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.models.transaction import TransactionType
from app.core.exceptions import BadRequestError
from app.services import own_transfers
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


class _FakeDb:
    def __init__(self, user=None, row=None):
        self.user, self.row, self.committed = user, row, False

    def get(self, model, key):
        return self.user

    def scalar(self, query):
        return self.row

    def commit(self):
        self.committed = True


def _row(kind, amount, account, day, description, imported=True):
    return SimpleNamespace(
        id=uuid.uuid4(), type=kind, amount=Decimal(amount), account_id=account,
        transaction_date=date(2026, 10, day), transfer_group_id=None, description=description,
        import_batch_id=uuid.uuid4() if imported else None, raw_data={},
    )


def _use_rows(monkeypatch, open_rows, singles=()):
    monkeypatch.setattr(own_transfers, "_open_imported_rows", lambda db, user_id: list(open_rows))
    monkeypatch.setattr(own_transfers, "_single_legs", lambda db, user_id: list(singles))


def test_nameless_transfers_are_marked_when_both_sides_match(monkeypatch):
    opay, nayapay = uuid.uuid4(), uuid.uuid4()
    out = _row(TransactionType.EXPENSE, "500", opay, 9, "Bank Transfer NAYAPAY | 03216171128")
    back = _row(TransactionType.INCOME, "500", nayapay, 9, "Incoming fund transfer from OPay-1551")
    _use_rows(monkeypatch, [out, back])

    marked = own_transfers.mark_own_transfers(_FakeDb(SimpleNamespace(full_name=NAME)), uuid.uuid4())

    assert {id(t) for t in marked} == {id(out), id(back)}
    assert out.transfer_group_id == back.transfer_group_id is not None


def test_a_nameless_transfer_with_no_other_side_is_left_alone(monkeypatch):
    lone = _row(TransactionType.EXPENSE, "500", uuid.uuid4(), 9, "Outgoing fund transfer to Ali Raza")
    _use_rows(monkeypatch, [lone])

    assert own_transfers.mark_own_transfers(_FakeDb(SimpleNamespace(full_name=NAME)), uuid.uuid4()) == []
    assert lone.transfer_group_id is None


def test_a_named_leg_pairs_with_a_nameless_one(monkeypatch):
    meezan, opay = uuid.uuid4(), uuid.uuid4()
    out = _row(TransactionType.EXPENSE, "100", meezan, 3, "Money Transferred to Abdul Moeed OPay")
    back = _row(TransactionType.INCOME, "100", opay, 3, "Bank Transfer MEZN | 02790107421474")
    _use_rows(monkeypatch, [out, back])

    own_transfers.mark_own_transfers(_FakeDb(SimpleNamespace(full_name=NAME)), uuid.uuid4())

    assert out.transfer_group_id == back.transfer_group_id is not None


def test_mark_as_transfer_links_the_other_side(monkeypatch):
    opay, nayapay = uuid.uuid4(), uuid.uuid4()
    out = _row(TransactionType.EXPENSE, "750", opay, 9, "Payment 03216171128")
    back = _row(TransactionType.INCOME, "750", nayapay, 10, "Received money")
    other = _row(TransactionType.INCOME, "750", opay, 9, "Refund")
    out.raw_data = {own_transfers.NOT_TRANSFER_FLAG: True}
    _use_rows(monkeypatch, [out, back, other])

    legs = own_transfers.mark_as_transfer(_FakeDb(row=out), uuid.uuid4(), out.id)

    assert legs == [out, back]
    assert out.transfer_group_id == back.transfer_group_id is not None
    assert other.transfer_group_id is None
    assert own_transfers.NOT_TRANSFER_FLAG not in out.raw_data


def test_mark_as_transfer_works_without_the_other_side(monkeypatch):
    out = _row(TransactionType.EXPENSE, "750", uuid.uuid4(), 9, "Payment")
    _use_rows(monkeypatch, [out])

    assert own_transfers.mark_as_transfer(_FakeDb(row=out), uuid.uuid4(), out.id) == [out]
    assert out.transfer_group_id is not None


def test_app_made_rows_cannot_be_marked(monkeypatch):
    row = _row(TransactionType.EXPENSE, "750", uuid.uuid4(), 9, "Payment", imported=False)
    _use_rows(monkeypatch, [])

    with pytest.raises(BadRequestError):
        own_transfers.mark_as_transfer(_FakeDb(row=row), uuid.uuid4(), row.id)
