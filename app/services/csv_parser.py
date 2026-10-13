import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.core.exceptions import BadRequestError
from app.models.transaction import TransactionType

MAX_AMOUNT = Decimal("9999999999.99")

DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d.%m.%Y",
    "%d %b %Y",
    "%d-%b-%Y",
    "%d %B %Y",
    "%d-%B-%Y",
    "%b %d %Y",
    "%B %d %Y",
    "%d/%m/%y",
    "%d-%m-%y",
    "%d-%b-%y",
    "%d %b %y",
    "%Y%m%d",
    "%m/%d/%Y",
)

ALIASES = {
    "date": (
        "date",
        "transaction date",
        "txn date",
        "posted date",
        "value date",
        "timestamp",
        "date time",
        "datetime",
        "transaction time",
    ),
    "description": (
        "description",
        "details",
        "narration",
        "memo",
        "particulars",
        "transaction details",
    ),
    "amount": (
        "amount",
        "transaction amount",
    ),
    "debit": (
        "debit",
        "withdrawal",
        "withdrawals",
        "dr",
    ),
    "credit": (
        "credit",
        "deposit",
        "deposits",
        "cr",
    ),
    "type": (
        "type",
        "kind",
        "transaction type",
    ),
    "balance": (
        "balance",
        "running balance",
        "closing balance",
        "available balance",
    ),
}

TYPE_WORDS = {
    "income": TransactionType.INCOME,
    "credit": TransactionType.INCOME,
    "cr": TransactionType.INCOME,
    "c": TransactionType.INCOME,
    "deposit": TransactionType.INCOME,
    "expense": TransactionType.EXPENSE,
    "debit": TransactionType.EXPENSE,
    "dr": TransactionType.EXPENSE,
    "d": TransactionType.EXPENSE,
    "withdrawal": TransactionType.EXPENSE,
}

# Words inside a bank's own type text ("Raast In", "IBFT Out", "Funds Received")
# that say which way the money moved.
INCOME_WORDS = {"in", "cr", "credit", "credited", "deposit", "received", "receive", "refund", "incoming"}
EXPENSE_WORDS = {
    "out", "dr", "debit", "debited", "withdrawal", "withdrawn", "sent", "send",
    "paid", "payment", "purchase", "pos", "charges", "fee", "outgoing",
}

# Banks name the same column in many ways ("Txn Date", "Transaction Details",
# "Withdrawal Amount", "Debit (PKR)"). A header is classified by the words it
# contains; the order matters, so "Debit Amount" is a debit column, not an
# amount column.
HEADER_KEYWORDS = (
    ("balance", ("balance",)),
    ("type", ("dr/cr", "cr/dr", "d/c", "c/d", "type", "kind")),
    ("debit", ("debit", "debits", "withdrawal", "withdrawals", "dr", "paid out", "money out", "outflow")),
    ("credit", ("credit", "credits", "deposit", "deposits", "cr", "paid in", "money in", "inflow")),
    ("date", ("date", "timestamp", "datetime", "date time")),
    (
        "description",
        ("description", "details", "detail", "narration", "narrative", "particulars", "memo", "remarks", "purpose"),
    ),
    ("amount", ("amount", "amt")),
)


def normalize_header(name: str) -> str:
    value = name.lower()
    value = re.sub(r"\((pkr|rs\.?|rupees|amount|amt)\)", " ", value)
    value = re.sub(r"[^a-z/&]+", " ", value)
    return " ".join(value.split())


def classify_header(name: str) -> str | None:
    """Return which field a header holds (date, description, amount, ...)."""
    value = normalize_header(name)

    if not value:
        return None

    for kind, aliases in ALIASES.items():
        if value in aliases:
            return kind

    for kind, keywords in HEADER_KEYWORDS:
        for keyword in keywords:
            if re.search(rf"(^| ){re.escape(keyword)}( |$)", value):
                return kind

    return None


def looks_like_header(cells: list[str]) -> bool:
    """A header row names a date and a description column and holds no figures."""
    named = [cell for cell in cells if cell and cell.strip()]

    if not named or any(ch.isdigit() for cell in named for ch in cell):
        return False

    kinds = {classify_header(cell) for cell in named}
    return "date" in kinds and "description" in kinds


@dataclass
class ColumnMapping:
    date: str | None = None
    description: str | None = None
    amount: str | None = None
    debit: str | None = None
    credit: str | None = None
    type: str | None = None
    balance: str | None = None
    date_format: str | None = None


@dataclass
class ParsedRow:
    row: int
    transaction_date: date
    description: str
    amount: Decimal
    type: TransactionType
    raw: dict
    balance: Decimal | None = None


@dataclass
class ParseResult:
    rows: list[ParsedRow] = field(default_factory=list)
    errors: list[tuple[int, str]] = field(default_factory=list)
    total: int = 0
    skipped: int = 0


def decode_content(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def resolve_columns(
    headers: list[str],
    requested: ColumnMapping,
) -> ColumnMapping:
    lookup = {
        h.strip().lower(): h
        for h in headers
        if h
    }

    resolved = ColumnMapping(
        date_format=requested.date_format
    )

    for name, names in ALIASES.items():
        explicit = getattr(requested, name)

        if explicit:
            column = lookup.get(explicit.strip().lower())

            if column is None:
                raise BadRequestError(
                    f"Column '{explicit}' was not found in the CSV header"
                )

            setattr(resolved, name, column)
        else:
            setattr(
                resolved,
                name,
                next(
                    (lookup[a] for a in names if a in lookup),
                    None,
                ),
            )

    taken = {getattr(resolved, name) for name in ALIASES if getattr(resolved, name)}

    for name in ALIASES:
        if getattr(resolved, name) or getattr(requested, name):
            continue

        match = next(
            (h for h in headers if h and h not in taken and classify_header(h) == name),
            None,
        )

        if match:
            setattr(resolved, name, match)
            taken.add(match)

    if not resolved.date or not resolved.description:
        raise BadRequestError(
            "CSV must contain a date column and a description column"
        )

    if not resolved.amount and not (
        resolved.debit or resolved.credit
    ):
        raise BadRequestError(
            "CSV must contain an amount column or debit/credit columns"
        )

    return resolved


def parse_amount(text: str) -> Decimal:
    """Read amounts as banks write them.

    A minus anywhere before the figure ("Rs -300", "- PKR100.00"), a trailing
    minus ("300-") or brackets ("(75.25)") make it negative. "1,250.50" and
    "1.234,56" are both read correctly. A comma alone separates thousands
    ("1,250") unless only one or two digits follow it ("12 345,67").
    """
    value = text.strip()
    match = re.search(r"\d(?:[\d.,]|\s(?=\d{3}\b))*", value)

    if not match:
        raise ValueError("amount is not a number")

    before = value[: match.start()]
    after = value[match.end():].strip()
    negative = "-" in before or ("(" in before and ")" in after) or after.startswith("-")

    digits = re.sub(r"\s", "", match.group()).rstrip(".,")

    if "," in digits and "." in digits:
        if digits.rfind(",") > digits.rfind("."):
            digits = digits.replace(".", "").replace(",", ".")
        else:
            digits = digits.replace(",", "")
    elif digits.count(".") > 1:
        digits = digits.replace(".", "")
    elif "," in digits and len(digits.rsplit(",", 1)[1]) <= 2:
        # A lone comma before one or two digits is a decimal comma ("12 345,67").
        digits = digits.replace(",", "")[: -len(digits.rsplit(",", 1)[1])] + "." + digits.rsplit(",", 1)[1]
    else:
        digits = digits.replace(",", "")

    try:
        number = Decimal(digits)
    except InvalidOperation as exc:
        raise ValueError("amount is not a number") from exc

    number = number.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return -number if negative else number


def parse_date(
    text: str,
    date_format: str | None,
) -> date:
    value = text.strip()

    formats = (
        (date_format,)
        if date_format
        else DATE_FORMATS
    )

    # Statements often append a time ("08 Sep 2026 03:26 PM"), so also try
    # the value with the time part removed.
    parts = value.replace("T", " ").replace(",", " ").split()
    candidates = [value, " ".join(parts)]

    for count in (3, 1):
        candidate = " ".join(parts[:count])

        if candidate and candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        for fmt in formats:
            try:
                return datetime.strptime(
                    candidate,
                    fmt,
                ).date()
            except ValueError:
                continue

    raise ValueError("invalid date format")


def _parse_side(text: str) -> Decimal | None:
    value = text.strip()

    if not value or value in {"-", "--"}:
        return None

    amount = abs(parse_amount(value))

    return amount if amount > 0 else None


def _parse_balance(
    row: dict,
    mapping: ColumnMapping,
) -> Decimal | None:
    text = (
        (row.get(mapping.balance) or "").strip()
        if mapping.balance
        else ""
    )

    if not text:
        return None

    try:
        return parse_amount(text)
    except ValueError as exc:
        raise ValueError(
            "balance is not a number"
        ) from exc


def _parse_row(
    row: dict,
    mapping: ColumnMapping,
) -> tuple[
    date,
    str,
    Decimal,
    TransactionType,
    Decimal | None,
]:
    description = " ".join(
        (row.get(mapping.description) or "").split()
    )

    if not description:
        raise ValueError("description is required")

    txn_date = parse_date(
        row.get(mapping.date) or "",
        mapping.date_format,
    )

    debit = (
        (row.get(mapping.debit) or "").strip()
        if mapping.debit
        else ""
    )

    credit = (
        (row.get(mapping.credit) or "").strip()
        if mapping.credit
        else ""
    )

    if (
        mapping.amount
        and (row.get(mapping.amount) or "").strip()
    ):
        amount = parse_amount(
            row[mapping.amount]
        )

        if (
            mapping.type
            and (row.get(mapping.type) or "").strip()
        ):
            txn_type = TYPE_WORDS.get(
                row[mapping.type].strip().lower()
            ) or _type_from_text(row[mapping.type])

            # Bank-specific types ("Raast In", "POS") are not income/expense
            # words; a signed amount (+270 / -270) already tells us which.
            if txn_type is None and _has_sign(
                row[mapping.amount]
            ):
                txn_type = (
                    TransactionType.EXPENSE
                    if amount < 0
                    else TransactionType.INCOME
                )

            if txn_type is None:
                raise ValueError(
                    "type must be INCOME or EXPENSE"
                )
        else:
            txn_type = _type_from_suffix(row[mapping.amount]) or (
                TransactionType.EXPENSE
                if amount < 0
                else TransactionType.INCOME
            )

        amount = abs(amount)

    elif debit or credit:
        debit_amount = _parse_side(debit)
        credit_amount = _parse_side(credit)

        if debit_amount and credit_amount:
            raise ValueError(
                "row has both debit and credit values"
            )

        amount = debit_amount or credit_amount

        if amount is None:
            raise ValueError(
                "amount must be greater than zero"
            )

        txn_type = (
            TransactionType.EXPENSE
            if debit_amount
            else TransactionType.INCOME
        )

    else:
        raise ValueError("amount is required")

    if amount <= 0:
        raise ValueError(
            "amount must be greater than zero"
        )

    if amount > MAX_AMOUNT:
        raise ValueError("amount is too large")

    return (
        txn_date,
        description[:300],
        amount,
        txn_type,
        _parse_balance(row, mapping),
    )


def parse_csv(
    text: str,
    requested: ColumnMapping,
) -> ParseResult:
    records = [
        record
        for record in csv.reader(io.StringIO(text))
    ]

    header_index = _find_header_index(
        records,
        requested,
    )

    if header_index is None:
        raise BadRequestError(
            "CSV file is empty"
        )

    headers = [
        cell.strip()
        for cell in records[header_index]
    ]

    mapping = resolve_columns(
        headers,
        requested,
    )

    data_rows = [
        dict(zip(headers, record))
        for record in records[header_index + 1:]
    ]

    mapped_columns = {
        column
        for column in (
            mapping.date,
            mapping.description,
            mapping.amount,
            mapping.debit,
            mapping.credit,
            mapping.type,
        )
        if column
    }

    result = ParseResult()

    for line_number, row in enumerate(
        data_rows,
        start=header_index + 2,
    ):
        if not any(
            (value or "").strip()
            for value in row.values()
            if isinstance(value, str)
        ):
            continue

        result.total += 1

        if mapping.debit or mapping.credit:
            debit_value = (
                (row.get(mapping.debit) or "").strip()
                if mapping.debit
                else ""
            )

            credit_value = (
                (row.get(mapping.credit) or "").strip()
                if mapping.credit
                else ""
            )

            if (
                _is_zero_or_empty_amount(debit_value)
                and _is_zero_or_empty_amount(credit_value)
            ):
                result.skipped += 1
                continue

        try:
            (
                txn_date,
                description,
                amount,
                txn_type,
                balance,
            ) = _parse_row(
                row,
                mapping,
            )
        except ValueError as exc:
            result.errors.append(
                (
                    line_number,
                    str(exc),
                )
            )
            continue

        raw = {
            key: value
            for key, value in row.items()
            if (
                key is not None
                and key not in mapped_columns
                and isinstance(value, str)
            )
        }

        result.rows.append(
            ParsedRow(
                line_number,
                txn_date,
                description,
                amount,
                txn_type,
                raw,
                balance,
            )
        )

    return result


def _is_zero_or_empty_amount(
    text: str,
) -> bool:
    value = text.strip()

    if not value or value in {"-", "--"}:
        return True

    try:
        return parse_amount(value) == 0
    except ValueError:
        return False


def _type_from_suffix(text: str) -> TransactionType | None:
    """'1,500.00 Dr' is money out and '1,500.00 Cr' is money in."""
    match = re.search(r"\b(dr|cr)\.?\s*$", text.strip(), re.IGNORECASE)

    if not match:
        return None

    return TransactionType.EXPENSE if match.group(1).lower() == "dr" else TransactionType.INCOME


def _type_from_text(text: str) -> TransactionType | None:
    words = set(re.findall(r"[a-z]+", text.lower()))
    income = bool(words & INCOME_WORDS)
    expense = bool(words & EXPENSE_WORDS)

    if income == expense:
        return None

    return TransactionType.INCOME if income else TransactionType.EXPENSE


def _has_sign(text: str) -> bool:
    value = text.strip()

    return value.startswith(("+", "-", "("))


def _find_header_index(
    records: list[list[str]],
    requested: ColumnMapping,
) -> int | None:
    """Locate the header row.

    Bank statements often start with account details (name, IBAN, statement
    period) before the real table, so the header is the first row that names
    a date column and a description column. If no row qualifies, fall back to
    the first non-empty row so the usual error is reported.
    """
    first_non_empty = None
    wanted = {
        name.strip().lower()
        for name in (requested.date, requested.description)
        if name
    }

    for index, record in enumerate(records):
        cells = [cell.strip() for cell in record if cell.strip()]

        if not cells:
            continue

        if first_non_empty is None:
            first_non_empty = index

        if wanted:
            if wanted <= {cell.lower() for cell in cells}:
                return index
        elif looks_like_header(cells):
            return index

    return first_non_empty
