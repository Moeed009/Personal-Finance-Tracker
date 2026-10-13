import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from statistics import median

from app.core.exceptions import BadRequestError

Row = list[str]
Table = list[list[str | None]]

RULED = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}

LINE_TOLERANCE = 3
HEADER_WORD_GAP = 6
HEADER_LINE_GAP = 16
WRAP_GAP_FACTOR = 2.2

BREAK = None

ROLE_KEYWORDS = (
    ("balance", ("balance", "banlance", "bal", "running balance")),
    ("debit", ("debit", "debits", "withdrawal", "withdrawals", "dr", "paid out", "money out", "outflow")),
    ("credit", ("credit", "credits", "deposit", "deposits", "cr", "paid in", "money in", "inflow")),
    ("type", ("type", "dr/cr", "cr/dr", "d/c", "c/d", "kind")),
    (
        "reference",
        ("id", "ref", "reference", "cheque", "chq", "instrument", "doc", "stan", "rrn", "receipt", "voucher"),
    ),
    ("date", ("date", "timestamp", "datetime", "time")),
    (
        "description",
        ("description", "details", "detail", "narration", "narrative", "particulars", "memo", "remarks", "purpose"),
    ),
    ("amount", ("amount", "amt")),
)
NUMERIC_ROLES = {"amount", "debit", "credit", "balance"}

INCOME_WORDS = {"in", "cr", "credit", "credited", "deposit", "received", "receive", "refund", "incoming"}
EXPENSE_WORDS = {
    "out", "dr", "debit", "debited", "withdrawal", "withdrawn", "sent", "send",
    "paid", "payment", "purchase", "pos", "charges", "fee", "outgoing",
}

MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
MONTH_WORD = rf"(?:{MONTHS})[a-z]*\.?"
DATE_PATTERNS = (
    (re.compile(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b"), "ymd"),
    (re.compile(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})\b"), "dmy"),
    (re.compile(rf"\b(\d{{1,2}})[\s\-]*({MONTH_WORD})[\s\-,]*(\d{{2,4}})\b", re.I), "d_mon_y"),
    (re.compile(rf"\b({MONTH_WORD})[\s\-]*(\d{{1,2}})(?:st|nd|rd|th)?,?[\s\-]*(\d{{4}})\b", re.I), "mon_d_y"),
)
TIME = re.compile(r"(?<![\d:])\d{1,2}:\d{2}(:\d{2})?(\s*(am|pm)\b)?,?", re.I)
NUMBER_TOKEN = re.compile(r"^[+\-(]?(rs\.?|pkr)?\s?[\d,]*\d(\.\d+)?\)?(cr|dr)?$", re.I)
AMOUNT = re.compile(r"\d[\d,]*(?:\.\d+)?")

SKIP_ROW = re.compile(
    r"^(brought forward|carried forward|balance (b/f|c/f|brought forward|carried forward)|b/f|c/f|"
    r"opening balance|page \d+( of \d+)?\b)"
)
END_ROW = re.compile(r"^(closing balance|totals?\b|total (debit|credit|amount)s?\b)")
FOOTER = re.compile(r"(disclaimer|www\.|https?://|@[a-z0-9-]+\.[a-z]|auto[- ]generated|computer[- ]generated)")


def pdf_to_csv_text(content: bytes, password: str | None = None) -> str:
    import pdfplumber

    try:
        pdf = pdfplumber.open(io.BytesIO(content), password=password or "")
    except Exception as exc:
        raise _open_error(exc, password) from exc

    with pdf:
        try:
            pages = list(pdf.pages)
            has_text = any((page.extract_text() or "").strip() for page in pages)
        except Exception as exc:
            raise _open_error(exc, password) from exc

        if not has_text:
            raise BadRequestError(
                "This PDF has no readable text. Scanned statements are not supported; "
                "download the statement from your bank's app or website instead"
            )

        ruled: Table = []

        for page in pages:
            for table in page.extract_tables(RULED) or []:
                ruled.extend(table)
                ruled.append(BREAK)

        candidates = [_records(_clean_rows(ruled)), _records(_layout_rows(pages))]

    best = max(candidates, key=len)

    if not best:
        raise BadRequestError(
            "Could not find a transaction table in this PDF. "
            "It needs columns for the date and the amount (or debit and credit)"
        )

    return _to_csv(best)


def tables_to_csv(tables: list[Table]) -> str:
    rows: Table = []

    for table in tables:
        rows.extend(table)
        rows.append(BREAK)

    records = _records(_clean_rows(rows))
    return _to_csv(records) if records else ""


@dataclass
class _Record:
    when: date
    description: str
    amount: Decimal
    sign: int | None
    balance: Decimal | None


@dataclass
class _Columns:
    roles: list[str | None]
    date: int
    amount: int | None
    debit: int | None
    credit: int | None
    balance: int | None
    type: int | None
    text: list[int]


def _records(rows: list[Row | None]) -> list[_Record]:
    records: list[_Record] = []
    columns: _Columns | None = None
    can_wrap = False

    for row in rows:
        if row is BREAK:
            can_wrap = False
            continue

        if _is_header(row):
            columns = _columns(row)
            can_wrap = False
            continue

        if columns is None:
            continue

        row = (row + [""] * len(columns.roles))[: len(columns.roles)]
        when, leftover = _parse_date(row[columns.date])
        description = " ".join(
            part for part in (leftover, _description(row, columns, keep_codes=when is None)) if part
        )
        lowered = description.lower()

        if END_ROW.match(lowered):
            break

        amounts = [
            row[i] for i in (columns.amount, columns.debit, columns.credit)
            if i is not None and _amount(row[i])[0]
        ]

        if when is None:
            text = description

            if not text and not amounts:
                continue

            has_balance = columns.balance is not None and _amount(row[columns.balance])[0] is not None
            is_wrapped_text = (
                can_wrap
                and records
                and text
                and not amounts
                and not has_balance
                and not SKIP_ROW.match(text.lower())
                and not FOOTER.search(text.lower())
            )

            if is_wrapped_text:
                records[-1].description = f"{records[-1].description} {text}".strip()
            else:
                can_wrap = False
            continue

        if SKIP_ROW.match(lowered) or not amounts:
            can_wrap = False
            continue

        record = _record(when, description, row, columns)

        if record is None:
            can_wrap = False
            continue

        records.append(record)
        can_wrap = True

    _resolve_signs(records)
    return records


def _record(when: date, description: str, row: Row, columns: _Columns) -> _Record | None:
    balance = _amount(row[columns.balance])[0] if columns.balance is not None else None

    if columns.debit is not None or columns.credit is not None:
        debit, debit_sign = _amount(row[columns.debit]) if columns.debit is not None else (None, None)
        credit, credit_sign = _amount(row[columns.credit]) if columns.credit is not None else (None, None)

        if debit and not credit:
            return _Record(when, description, debit, debit_sign or -1, balance)

        if credit and not debit:
            return _Record(when, description, credit, credit_sign or 1, balance)

        if debit and credit:
            net = credit - debit
            return _Record(when, description, abs(net), 1 if net > 0 else -1, balance) if net else None

    if columns.amount is not None:
        value, sign = _amount(row[columns.amount])

        if value:
            if sign is None and columns.type is not None:
                sign = _sign_from_words(row[columns.type])

            return _Record(when, description, value, sign, balance)

    return None


def _resolve_signs(records: list[_Record]) -> None:
    newest_first = len(records) > 1 and records[0].when > records[-1].when
    ordered = list(reversed(records)) if newest_first else records

    for previous, current in zip([None, *ordered], ordered):
        if current.sign is not None:
            continue

        if previous and previous.balance is not None and current.balance is not None:
            change = current.balance - previous.balance

            if abs(abs(change) - current.amount) < Decimal("0.02"):
                current.sign = 1 if change > 0 else -1
                continue

        current.sign = 1


def _to_csv(records: list[_Record]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Description", "Amount", "Balance"])

    for record in records:
        writer.writerow([
            record.when.isoformat(),
            record.description,
            f"{record.amount * (record.sign or 1):.2f}",
            "" if record.balance is None else f"{record.balance:.2f}",
        ])

    return buffer.getvalue()


def _role(name: str) -> str | None:
    value = re.sub(r"\((pkr|rs\.?|rupees|amount|amt)\)", " ", name.lower())
    value = " ".join(re.sub(r"[^a-z/&]+", " ", value).split())

    for role, keywords in ROLE_KEYWORDS:
        for keyword in keywords:
            if re.search(rf"(^| ){re.escape(keyword)}( |$)", value):
                return role

    return None


def _is_header(row: Row) -> bool:
    cells = [cell for cell in row if cell]

    if len(cells) < 3 or any(ch.isdigit() for cell in cells for ch in cell):
        return False

    roles = {_role(cell) for cell in cells}
    return "date" in roles and bool(roles & {"amount", "debit", "credit"})


def _columns(header: Row) -> _Columns:
    roles = [_role(cell) if cell else None for cell in header]

    def first(role: str, avoid: str | None = None) -> int | None:
        matches = [i for i, r in enumerate(roles) if r == role]
        preferred = [i for i in matches if not (avoid and avoid in header[i].lower())]
        return (preferred or matches or [None])[0]

    date_col = first("date", avoid="value")
    has_description = "description" in roles
    text = [
        i for i, role in enumerate(roles)
        if role in ("description", "reference", None) or (role == "type" and not has_description)
    ]

    return _Columns(
        roles=roles,
        date=date_col,
        amount=first("amount"),
        debit=first("debit"),
        credit=first("credit"),
        balance=first("balance"),
        type=first("type"),
        text=text,
    )


def _description(row: Row, columns: _Columns, keep_codes: bool = False) -> str:
    parts = []

    for i in columns.text:
        cell = row[i].strip()

        is_code = columns.roles[i] == "reference" and " " not in cell and re.search(r"\d", cell)

        if cell and (keep_codes or not is_code):
            parts.append(cell)

    return " ".join(" ".join(parts).split())


def _parse_date(text: str) -> tuple[date | None, str]:
    value = " ".join((text or "").split())

    for pattern, order in DATE_PATTERNS:
        match = pattern.search(value)

        if not match:
            continue

        a, b, c = match.groups()

        try:
            if order == "ymd":
                found = date(int(a), int(b), int(c))
            elif order == "dmy":
                day, month = int(a), int(b)

                if month > 12 and day <= 12:
                    day, month = month, day

                found = date(_year(c), month, day)
            elif order == "d_mon_y":
                found = _month_date(c, b, a)
            else:
                found = _month_date(c, a, b)
        except ValueError:
            continue

        return found, _without_time(value[: match.start()] + " " + value[match.end():])

    return None, _without_time(value)


def _without_time(text: str) -> str:
    return " ".join(TIME.sub(" ", text).split())


def _year(text: str) -> int:
    year = int(text)
    return year + 2000 if year < 100 else year


def _month_date(year: str, month: str, day: str) -> date:
    month_name = month.rstrip(".")[:3].title()
    return datetime.strptime(f"{int(day)} {month_name} {_year(year)}", "%d %b %Y").date()


def _amount(text: str | None) -> tuple[Decimal | None, int | None]:
    value = " ".join((text or "").split())
    match = AMOUNT.search(value)

    if not match:
        return None, None

    try:
        number = Decimal(match.group().replace(",", ""))
    except InvalidOperation:
        return None, None

    if not number:
        return None, None

    before, after = value[: match.start()].strip().lower(), value[match.end():].strip().lower()
    sign = None

    if before.startswith("-") or before.startswith("(") or after.endswith("-"):
        sign = -1
    elif before.startswith("+"):
        sign = 1
    elif re.match(r"^dr\b", after):
        sign = -1
    elif re.match(r"^cr\b", after):
        sign = 1

    return number.quantize(Decimal("0.01")), sign


def _sign_from_words(text: str) -> int | None:
    words = set(re.findall(r"[a-z]+", (text or "").lower()))
    income, expense = bool(words & INCOME_WORDS), bool(words & EXPENSE_WORDS)

    if income == expense:
        return None

    return 1 if income else -1


def _clean_rows(rows: Table) -> list[Row | None]:
    cleaned: list[Row | None] = []

    for row in rows:
        if row is BREAK:
            cleaned.append(BREAK)
            continue

        cells = [" ".join((cell or "").split()) for cell in row]

        if any(cells):
            cleaned.append(cells)

    return cleaned


def _layout_rows(pages) -> list[Row | None]:
    rows: list[Row | None] = []
    columns: list[tuple[str, float]] | None = None

    for page in pages:
        lines = _lines(page.extract_words())
        start = 0

        for index, line in enumerate(lines):
            header = _header_cells(line)

            if not _is_header([name for name, _ in header]):
                continue

            names = [name for name, _ in header]
            start = index + 1
            second = lines[index + 1] if index + 1 < len(lines) else []

            if (
                second
                and second[0]["top"] - line[0]["top"] < HEADER_LINE_GAP
                and not any(ch.isdigit() for word in second for ch in word["text"])
            ):
                for word in second:
                    column = _column_for(word, header, set())
                    names[column] = f"{names[column]} {word['text']}"
                start = index + 2

            columns = list(zip(names, [x0 for _, x0 in header]))
            break

        if columns is None:
            continue

        rows.append(BREAK)
        rows.append([name for name, _ in columns])

        numeric = {i for i, (name, _) in enumerate(columns) if _role(name) in NUMERIC_ROLES}
        body = lines[start:]
        gaps = [b[0]["top"] - a[0]["top"] for a, b in zip(body, body[1:]) if b[0]["top"] > a[0]["top"]]
        usual_gap = median(gaps) if gaps else 0

        for previous, line in zip([None, *body], body):
            if previous and usual_gap and line[0]["top"] - previous[0]["top"] > usual_gap * WRAP_GAP_FACTOR:
                rows.append(BREAK)

            cells = [""] * len(columns)

            for word in line:
                column = _column_for(word, columns, numeric)
                cells[column] = f"{cells[column]} {word['text']}".strip()

            rows.append(cells)

    return rows


def _lines(words: list[dict]) -> list[list[dict]]:
    lines: list[list[dict]] = []

    for word in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if lines and abs(lines[-1][0]["top"] - word["top"]) <= LINE_TOLERANCE:
            lines[-1].append(word)
        else:
            lines.append([word])

    return [sorted(line, key=lambda w: w["x0"]) for line in lines]


def _header_cells(line: list[dict]) -> list[tuple[str, float]]:
    cells: list[list] = []

    for word in line:
        if cells and word["x0"] - cells[-1][2] <= HEADER_WORD_GAP:
            cells[-1][0] += f" {word['text']}"
            cells[-1][2] = word["x1"]
        else:
            cells.append([word["text"], word["x0"], word["x1"]])

    return [(" ".join(text.split()), x0) for text, x0, _ in cells]


def _column_for(word: dict, columns: list[tuple[str, float]], numeric: set[int]) -> int:
    starts = [x0 for _, x0 in columns]
    index = max((i for i, x0 in enumerate(starts) if x0 <= word["x0"] + 2), default=0)

    if NUMBER_TOKEN.match(word["text"]):
        reach = [i for i, x0 in enumerate(starts) if x0 < word["x1"] and i in numeric and i > index]

        if reach:
            index = max(reach)

    return index


def _open_error(exc: Exception, password: str | None) -> BadRequestError:
    seen: list[str] = []
    current: BaseException | None = exc

    while current is not None and len(seen) < 10:
        seen.append(f"{type(current).__name__} {current!r}")
        seen.extend(type(arg).__name__ for arg in current.args if isinstance(arg, BaseException))
        current = current.__cause__ or current.__context__

    if "password" in " ".join(seen).lower():
        if password:
            return BadRequestError("The PDF password is incorrect")
        return BadRequestError("This PDF is password-protected. Enter its password and try again")

    return BadRequestError("Could not read this PDF file")