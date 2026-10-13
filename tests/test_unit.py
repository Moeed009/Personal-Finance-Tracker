import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.core.exceptions import BadRequestError
from app.core.money import ZERO, money, percent
from app.models.transaction import TransactionType
from app.services.categorization import derive_merchant, match_category_name
from app.services.csv_parser import ColumnMapping, classify_header, parse_amount, parse_csv, parse_date
from app.services.import_service import compute_dedupe_hash
from app.services.pdf_parser import tables_to_csv
from app.services.insight_service import _transaction_threshold
from app.services.recurring_service import RecurringFrequency, evaluate_series

EXPENSE = TransactionType.EXPENSE
INCOME = TransactionType.INCOME


class TestMoney:
    def test_rounds_half_up_to_two_places(self):
        assert money("10.005") == Decimal("10.01")
        assert money("10.004") == Decimal("10.00")

    def test_percent(self):
        assert percent(Decimal("25"), Decimal("200")) == Decimal("12.50")

    def test_percent_with_zero_whole_returns_zero(self):
        assert percent(Decimal("5"), Decimal("0")) == ZERO


class TestCategorization:
    @pytest.mark.parametrize(
        "description, expected",
        [
            ("FoodPanda order #4521", "Food"),
            ("Careem ride to office", "Transport"),
            ("K-Electric bill", "Bills"),
            ("Netflix subscription", "Entertainment"),
            ("Zakat payment", "Charity"),
        ],
    )
    def test_expense_keywords(self, description, expected):
        assert match_category_name(description, EXPENSE) == expected

    def test_income_keywords(self):
        assert match_category_name("Monthly salary credited", INCOME) == "Salary"

    def test_unknown_description_returns_none(self):
        assert match_category_name("random text xyz", EXPENSE) is None

    def test_keyword_must_be_a_whole_word(self):
        assert match_category_name("current account fee", EXPENSE) is None

    def test_income_keyword_not_used_for_expense(self):
        assert match_category_name("salary", EXPENSE) is None

    def test_derive_merchant_strips_numbers_and_symbols(self):
        assert derive_merchant("FoodPanda #4521") == "foodpanda"

    def test_derive_merchant_returns_none_for_only_digits(self):
        assert derive_merchant("12345 ***") is None


class TestParseAmount:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("1,250.50", Decimal("1250.50")),
            ("Rs. 500", Decimal("500.00")),
            ("-300", Decimal("-300.00")),
            ("(75.25)", Decimal("-75.25")),
            ("10.005", Decimal("10.01")),
        ],
    )
    def test_valid_amounts(self, text, expected):
        assert parse_amount(text) == expected

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            parse_amount("abc")


class TestParseDate:
    @pytest.mark.parametrize(
        "text",
        ["2026-03-15", "15/03/2026", "15-03-2026", "15 Mar 2026"],
    )
    def test_supported_formats(self, text):
        assert parse_date(text, None) == date(2026, 3, 15)

    def test_explicit_format_is_respected(self):
        assert parse_date("03/04/2026", "%m/%d/%Y") == date(2026, 3, 4)

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError):
            parse_date("not-a-date", None)


class TestParseCsv:
    def test_single_amount_column_infers_type_from_sign(self):
        text = "Date,Description,Amount\n2026-03-01,Salary,50000\n2026-03-02,KFC,-850\n"
        result = parse_csv(text, ColumnMapping())

        assert result.total == 2
        assert result.errors == []
        assert result.rows[0].type == INCOME
        assert result.rows[0].amount == Decimal("50000.00")
        assert result.rows[1].type == EXPENSE
        assert result.rows[1].amount == Decimal("850.00")

    def test_debit_credit_columns(self):
        text = "Date,Narration,Debit,Credit\n2026-03-01,Rent,15000,\n2026-03-02,Salary,,60000\n"
        result = parse_csv(text, ColumnMapping())

        assert [r.type for r in result.rows] == [EXPENSE, INCOME]
        assert [r.amount for r in result.rows] == [Decimal("15000.00"), Decimal("60000.00")]

    def test_bad_rows_are_reported_not_fatal(self):
        text = (
            "Date,Description,Amount\n"
            "2026-03-01,Good row,-100\n"
            "bad-date,Bad date,-100\n"
            "2026-03-03,,-100\n"
            "2026-03-04,Zero,0\n"
        )
        result = parse_csv(text, ColumnMapping())

        assert result.total == 4
        assert len(result.rows) == 1
        assert [line for line, _ in result.errors] == [3, 4, 5]

    def test_row_with_both_debit_and_credit_is_rejected(self):
        text = "Date,Description,Debit,Credit\n2026-03-01,Odd,100,200\n"
        result = parse_csv(text, ColumnMapping())

        assert result.rows == []
        assert result.errors[0][1] == "row has both debit and credit values"

    def test_blank_lines_are_ignored(self):
        text = "Date,Description,Amount\n2026-03-01,A,-10\n,,\n"
        assert parse_csv(text, ColumnMapping()).total == 1

    def test_missing_required_columns_raises(self):
        with pytest.raises(BadRequestError):
            parse_csv("Foo,Bar\n1,2\n", ColumnMapping())

    def test_unknown_explicit_column_raises(self):
        text = "Date,Description,Amount\n2026-03-01,A,-10\n"
        with pytest.raises(BadRequestError):
            parse_csv(text, ColumnMapping(amount="Total"))

    def test_extra_columns_go_to_raw(self):
        text = "Date,Description,Amount,Ref\n2026-03-01,A,-10,TX99\n"
        row = parse_csv(text, ColumnMapping()).rows[0]
        assert row.raw == {"Ref": "TX99"}


class TestDedupeHash:
    ACCOUNT = uuid.UUID("11111111-1111-1111-1111-111111111111")

    def test_same_input_gives_same_hash(self):
        a = compute_dedupe_hash(self.ACCOUNT, date(2026, 3, 1), Decimal("100"), "KFC")
        b = compute_dedupe_hash(self.ACCOUNT, date(2026, 3, 1), Decimal("100.00"), "KFC")
        assert a == b

    def test_description_case_and_spacing_are_normalized(self):
        a = compute_dedupe_hash(self.ACCOUNT, date(2026, 3, 1), Decimal("100"), "KFC  DHA")
        b = compute_dedupe_hash(self.ACCOUNT, date(2026, 3, 1), Decimal("100"), " kfc dha ")
        assert a == b

    def test_different_amount_gives_different_hash(self):
        a = compute_dedupe_hash(self.ACCOUNT, date(2026, 3, 1), Decimal("100"), "KFC")
        b = compute_dedupe_hash(self.ACCOUNT, date(2026, 3, 1), Decimal("101"), "KFC")
        assert a != b

    def test_different_account_gives_different_hash(self):
        other = uuid.UUID("22222222-2222-2222-2222-222222222222")
        a = compute_dedupe_hash(self.ACCOUNT, date(2026, 3, 1), Decimal("100"), "KFC")
        b = compute_dedupe_hash(other, date(2026, 3, 1), Decimal("100"), "KFC")
        assert a != b


class TestRecurringDetection:
    def test_monthly_series_is_detected(self):
        dates = [date(2026, 1, 5), date(2026, 2, 4), date(2026, 3, 6)]
        amounts = [Decimal("500")] * 3

        assert evaluate_series(dates, amounts) == (RecurringFrequency.MONTHLY, Decimal("500.00"))

    def test_weekly_series_is_detected(self):
        dates = [date(2026, 3, 1), date(2026, 3, 8), date(2026, 3, 15), date(2026, 3, 22)]
        amounts = [Decimal("200")] * 4

        frequency, _ = evaluate_series(dates, amounts)
        assert frequency == RecurringFrequency.WEEKLY

    def test_fewer_than_three_occurrences_is_not_recurring(self):
        assert evaluate_series([date(2026, 1, 5), date(2026, 2, 4)], [Decimal("500")] * 2) is None

    def test_irregular_gaps_are_not_recurring(self):
        dates = [date(2026, 1, 1), date(2026, 1, 10), date(2026, 3, 20)]
        assert evaluate_series(dates, [Decimal("500")] * 3) is None

    def test_amount_variation_above_ten_percent_is_not_recurring(self):
        dates = [date(2026, 1, 5), date(2026, 2, 4), date(2026, 3, 6)]
        amounts = [Decimal("500"), Decimal("500"), Decimal("800")]
        assert evaluate_series(dates, amounts) is None

    def test_small_gap_drift_is_tolerated(self):
        dates = [date(2026, 1, 5), date(2026, 2, 6), date(2026, 3, 5)]
        assert evaluate_series(dates, [Decimal("500")] * 3) is not None


class TestUnusualThreshold:
    def test_needs_at_least_five_transactions(self):
        assert _transaction_threshold([Decimal("100")] * 4) is None

    def test_constant_history_threshold_equals_the_value(self):
        assert _transaction_threshold([Decimal("100")] * 5) == Decimal("100.00")

    def test_threshold_is_mean_plus_two_standard_deviations(self):
        history = [Decimal("10")] * 4 + [Decimal("100")]
        assert _transaction_threshold(history) == Decimal("100.00")

class TestPdfTables:
    def test_header_found_after_preamble_and_wrapped_description_joined(self):
        tables = [[
            ["Customer Name", "Abdul Moeed", None],
            ["Date", "Description", "Amount"],
            ["2026-09-01", "Incoming transfer", "+500"],
            [None, "from Meezan", None],
            ["2026-09-02", "KFC\nLahore", "-850"],
        ]]
        result = parse_csv(tables_to_csv(tables), ColumnMapping())

        assert result.errors == []
        assert [r.description for r in result.rows] == ["Incoming transfer from Meezan", "KFC Lahore"]
        assert [r.type for r in result.rows] == [INCOME, EXPENSE]

    def test_header_repeated_on_each_page_is_dropped(self):
        page = [["Date", "Description", "Amount"], ["2026-09-01", "A", "-10"]]
        result = parse_csv(tables_to_csv([page, page]), ColumnMapping())

        assert result.total == 2
        assert result.errors == []

    def test_no_header_gives_empty_text(self):
        assert tables_to_csv([[["Name", "Value"], ["a", "1"]]]) == ""

    def test_bank_layout_with_folded_columns_and_page_furniture(self):
        page = [
            ["DATE", "INSTRUMENT/ DOC NO.", "DETAILS", "DEBIT", "CREDIT", "BALANCE"],
            [None, "Brought Forward", None, None, None, "1,811.53"],
            ["31/08/2026", None, "Opening Balance", None, None, "427.53"],
            ["14/09/2026", "4187154691 RAAST", "P2P FT, Digital", "1,130.00", None, "681.53"],
            [None, "PK51ASCM000063,", "USAMA", None, None, None],
            [None, "RAFIQUE", None, None, None, None],
            [None, None, None, None, None, "681.53"],
            [None, "Carried Forward", None, None, None, None],
            [None, "Page 1 of 5", None, None, None, None],
            ["30/09/2026", None, "Closing Balance", None, None, "681.53"],
            [None, "Totals:", None, "1,130.00", None, None],
        ]
        result = parse_csv(tables_to_csv([page]), ColumnMapping())

        assert result.errors == []
        assert len(result.rows) == 1
        assert result.rows[0].description == "4187154691 RAAST P2P FT, Digital PK51ASCM000063, USAMA RAFIQUE"
        assert result.rows[0].type == EXPENSE
        assert result.rows[0].amount == Decimal("1130.00")


class TestBankFormats:
    @pytest.mark.parametrize(
        "header, kind",
        [
            ("Txn Date", "date"),
            ("Date & Time", "date"),
            ("Transaction Details", "description"),
            ("Particulars", "description"),
            ("Debit (PKR)", "debit"),
            ("Withdrawal Amount", "debit"),
            ("Deposit Amount", "credit"),
            ("Amount (Rs.)", "amount"),
            ("Running Balance", "balance"),
            ("Dr/Cr", "type"),
            ("Cheque No.", None),
        ],
    )
    def test_header_names_are_recognised(self, header, kind):
        assert classify_header(header) == kind

    def test_debit_credit_columns_with_bank_names(self):
        text = (
            "Transaction Date,Value Date,Narration,Cheque No,Debit (PKR),Credit (PKR),Balance (PKR)\n"
            "05/09/2026,05/09/2026,FOODPANDA,,1500.00,,8500.00\n"
            "06/09/2026,06/09/2026,SALARY,,,50000.00,58500.00\n"
        )
        result = parse_csv(text, ColumnMapping())

        assert result.errors == []
        assert [r.type for r in result.rows] == [EXPENSE, INCOME]
        assert result.rows[1].balance == Decimal("58500.00")

    def test_dr_cr_suffix_on_amount(self):
        text = 'Date,Particulars,Amount\n05-Sep-2026,KFC,"1,560.00 Dr"\n06-Sep-2026,Transfer,2000.00 CR\n'
        result = parse_csv(text, ColumnMapping())

        assert [r.type for r in result.rows] == [EXPENSE, INCOME]
        assert [r.amount for r in result.rows] == [Decimal("1560.00"), Decimal("2000.00")]

    def test_bank_type_words_and_dates_with_commas(self):
        text = (
            "Date & Time,Transaction Type,Description,Amount (Rs.)\n"
            '"Sep 05, 2026 10:30 AM",Money Received,From Ali,500\n'
            '"Sep 06, 2026 11:00 AM",Bill Payment,K-Electric,1200\n'
        )
        result = parse_csv(text, ColumnMapping())

        assert result.errors == []
        assert [r.type for r in result.rows] == [INCOME, EXPENSE]
        assert result.rows[0].transaction_date == date(2026, 9, 5)
