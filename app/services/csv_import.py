import csv
import hashlib
import io
import re
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

from app.models.transaction import TransactionType
from app.schemas.imports import ColumnMapping, RowError

MAX_IMPORT_ROWS = 10_000
MERCHANT_MAX_LENGTH = 255
MAX_AMOUNT = Decimal("10000000000")
DELIMITERS = ",;\t|"
ENCODINGS = ("utf-8-sig", "cp1252")
DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%d-%b-%Y",
    "%d %b %Y",
    "%d/%m/%y",
)

_CURRENCY = re.compile(r"(?i)(?:pkr|rs|usd|inr|eur|gbp)\.?|[$€£₨]")
_AMOUNT_FORMAT = re.compile(r"^\(?[-+]?(?:\d+\.?\d*|\.\d+)\)?$")

_HEADER_ALIASES = {
    "date": ("date", "transaction date", "txn date", "posting date", "value date"),
    "description": ("description", "details", "narration", "memo", "particulars", "remarks"),
    "merchant": ("merchant", "payee", "vendor"),
    "amount": ("amount", "amt", "transaction amount"),
    "debit": ("debit", "withdrawal", "withdrawals", "dr"),
    "credit": ("credit", "deposit", "deposits", "cr"),
}


class CsvParseError(ValueError):
    pass


class RowValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedTransaction:
    row_number: int
    transaction_date: date
    amount: Decimal
    transaction_type: TransactionType
    description: str | None
    merchant: str | None
    dedupe_hash: str
    raw_data: dict[str, str]


def _decode(content: bytes) -> str:
    for encoding in ENCODINGS:
        try:
            text = content.decode(encoding)
        except UnicodeDecodeError:
            continue
        if "\x00" in text:
            break
        return text
    raise CsvParseError("File is not a valid CSV. Save it as a UTF-8 CSV and try again")


def _detect_delimiter(text: str) -> str:
    try:
        return csv.Sniffer().sniff(text[:4096], delimiters=DELIMITERS).delimiter
    except csv.Error:
        return ","


def read_csv(content: bytes) -> tuple[list[str], list[tuple[int, dict[str, str]]]]:
    text = _decode(content)
    reader = csv.reader(io.StringIO(text), delimiter=_detect_delimiter(text))

    try:
        raw_headers = next(reader)
    except StopIteration:
        raise CsvParseError("CSV file is empty") from None

    columns = [
        (index, name.strip()) for index, name in enumerate(raw_headers) if name.strip()
    ]
    if not columns:
        raise CsvParseError("CSV header row is empty")

    headers = [name for _, name in columns]
    if len(set(headers)) != len(headers):
        raise CsvParseError("CSV header contains duplicate column names")

    rows: list[tuple[int, dict[str, str]]] = []
    for values in reader:
        if not any(value.strip() for value in values):
            continue
        if len(rows) >= MAX_IMPORT_ROWS:
            raise CsvParseError(f"CSV has more than {MAX_IMPORT_ROWS} rows")
        row = {
            name: values[index].strip() if index < len(values) else ""
            for index, name in columns
        }
        rows.append((reader.line_num, row))

    if not rows:
        raise CsvParseError("CSV file has no data rows")

    return headers, rows


def validate_mapping(mapping: ColumnMapping, headers: list[str]) -> None:
    referenced = (
        mapping.date,
        mapping.description,
        mapping.merchant,
        mapping.amount,
        mapping.debit,
        mapping.credit,
    )
    missing = [column for column in referenced if column and column not in headers]
    if missing:
        raise CsvParseError(f"Mapped columns not found in CSV: {', '.join(missing)}")

    if mapping.date_format:
        sample = datetime(2025, 3, 1)
        try:
            datetime.strptime(sample.strftime(mapping.date_format), mapping.date_format)
        except ValueError:
            raise CsvParseError(f"Invalid date_format '{mapping.date_format}'") from None


def _find_header(headers: list[str], aliases: Iterable[str]) -> str | None:
    lookup = {header.lower(): header for header in headers}
    for alias in aliases:
        if alias in lookup:
            return lookup[alias]
    return None


def suggest_mapping(headers: list[str]) -> ColumnMapping | None:
    found = {
        field: _find_header(headers, aliases) for field, aliases in _HEADER_ALIASES.items()
    }
    if not found["date"]:
        return None
    if found["amount"]:
        found["debit"] = None
        found["credit"] = None
    elif not (found["debit"] and found["credit"]):
        return None
    return ColumnMapping(**found)


def _parse_date(value: str, date_format: str | None) -> date:
    if not value:
        raise RowValidationError("Date is missing")
    formats = (date_format,) if date_format else DATE_FORMATS
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise RowValidationError(f"Invalid date '{value}'")


def _parse_amount(value: str) -> Decimal:
    if not value:
        raise RowValidationError("Amount is missing")
    cleaned = _CURRENCY.sub("", value).replace(",", "").replace(" ", "")
    if not _AMOUNT_FORMAT.match(cleaned):
        raise RowValidationError(f"Invalid amount '{value}'")
    amount = Decimal(cleaned.strip("()"))
    if cleaned.startswith("("):
        amount = -abs(amount)
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if abs(amount) >= MAX_AMOUNT:
        raise RowValidationError("Amount is too large")
    return amount


def _resolve_amount_and_type(
    mapping: ColumnMapping, row: dict[str, str]
) -> tuple[Decimal, TransactionType]:
    if mapping.amount:
        signed = _parse_amount(row[mapping.amount])
        if signed == 0:
            raise RowValidationError("Amount cannot be zero")
        transaction_type = TransactionType.EXPENSE if signed < 0 else TransactionType.INCOME
        return abs(signed), transaction_type

    debit_value = row[mapping.debit]
    credit_value = row[mapping.credit]
    debit = _parse_amount(debit_value) if debit_value else Decimal("0")
    credit = _parse_amount(credit_value) if credit_value else Decimal("0")

    if debit and credit:
        raise RowValidationError("Both debit and credit have values")
    if not debit and not credit:
        raise RowValidationError("Debit and credit are both empty or zero")
    if debit:
        return abs(debit), TransactionType.EXPENSE
    return abs(credit), TransactionType.INCOME


def _optional(row: dict[str, str], column: str | None) -> str | None:
    if not column:
        return None
    return row[column] or None


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").lower().split())


def _dedupe_hash(
    account_id: uuid.UUID,
    transaction_date: date,
    amount: Decimal,
    transaction_type: TransactionType,
    description: str | None,
    occurrence: int,
) -> str:
    key = "|".join(
        (
            str(account_id),
            transaction_date.isoformat(),
            f"{amount:.2f}",
            transaction_type.value,
            _normalize_text(description),
            str(occurrence),
        )
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def parse_rows(
    rows: list[tuple[int, dict[str, str]]],
    mapping: ColumnMapping,
    account_id: uuid.UUID,
) -> tuple[list[ParsedTransaction], list[RowError]]:
    parsed: list[ParsedTransaction] = []
    errors: list[RowError] = []
    seen: Counter = Counter()

    for row_number, row in rows:
        try:
            transaction_date = _parse_date(row[mapping.date], mapping.date_format)
            amount, transaction_type = _resolve_amount_and_type(mapping, row)
        except RowValidationError as exc:
            errors.append(RowError(row_number=row_number, reason=str(exc)))
            continue

        description = _optional(row, mapping.description)
        merchant = _optional(row, mapping.merchant)
        if merchant:
            merchant = merchant[:MERCHANT_MAX_LENGTH]

        base_key = (transaction_date, amount, transaction_type, _normalize_text(description))
        occurrence = seen[base_key]
        seen[base_key] += 1

        parsed.append(
            ParsedTransaction(
                row_number=row_number,
                transaction_date=transaction_date,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                merchant=merchant,
                dedupe_hash=_dedupe_hash(
                    account_id,
                    transaction_date,
                    amount,
                    transaction_type,
                    description,
                    occurrence,
                ),
                raw_data=row,
            )
        )

    return parsed, errors