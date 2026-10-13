"""Turn a PDF bank statement into CSV text for the CSV parser.

The PDF's transaction table is extracted with pdfplumber and written out as
CSV, so PDF imports go through exactly the same parsing, validation,
duplicate detection and balance rules as CSV imports.
"""

import csv
import io
import re

from app.core.exceptions import BadRequestError
from app.services.csv_parser import classify_header, looks_like_header

Table = list[list[str | None]]

# Tables drawn with cell borders. Statements without borders are read from
# word positions instead (see _layout_tables).
RULED = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}

LINE_TOLERANCE = 3  # points: words this close vertically are on one line
HEADER_WORD_GAP = 6  # points: closer header words form one name ("Txn Date")
HEADER_LINE_GAP = 16  # points: a header's second line ("Value" / "Date")
NUMBER = re.compile(r"^[+\-(]?(rs\.?|pkr)?\s?[\d,]+(\.\d+)?\)?(cr|dr)?$", re.IGNORECASE)


# Rows that are not transactions.
PAGE_ROW = re.compile(
    r"^(brought forward|carried forward|balance (b/f|c/f|brought forward|carried forward)|page \d+( of \d+)?)\b"
)
OPENING_ROW = re.compile(r"^(opening balance|balance brought forward|b/f balance)\b")
END_ROW = re.compile(r"^(closing balance|totals?\b)")


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

        ruled: list[Table] = []

        for page in pages:
            ruled.extend(page.extract_tables(RULED) or [])

        for tables in (ruled, _layout_tables(pages)):
            text = tables_to_csv(tables)

            if text:
                return text

    raise BadRequestError(
        "Could not find a transaction table in this PDF. "
        "It needs columns for the date, description and amount"
    )


def tables_to_csv(tables: list[Table]) -> str:
    """Join the extracted tables into one CSV, starting at the header row.

    Returns an empty string when no header row (a date column and a
    description column) is found. Along the way it:

    - drops header rows repeated on later pages,
    - folds columns the parser does not use (such as "Instrument / Doc No.")
      into the description, since banks often print the description across
      them,
    - joins a description that wrapped onto following lines back onto its row,
    - drops page furniture such as "Brought Forward" or "Page 2 of 5", and
      stops at the closing balance or totals row.
    """
    rows = [
        [_clean(cell) for cell in row]
        for table in tables
        for row in table
    ]
    rows = [row for row in rows if any(row)]

    header_at = next((i for i, row in enumerate(rows) if _is_header(row)), None)

    if header_at is None:
        return ""

    header = rows[header_at]
    names = [cell.lower() for cell in header]
    date_col = _column(names, "date")
    description_col = _column(names, "description")
    folded = {i for i, name in enumerate(header) if classify_header(name) is None}
    keep = [i for i in range(len(header)) if i not in folded]
    description_parts = sorted(folded | {description_col})

    output: list[list[str]] = [[header[i] for i in keep]]
    out_date = keep.index(date_col)
    out_description = keep.index(description_col)

    for row in rows[header_at + 1:]:
        if [cell.lower() for cell in row] == names:
            continue

        row = (row + [""] * len(header))[: len(header)]
        row[description_col] = " ".join(row[i] for i in description_parts if row[i])
        row = [row[i] for i in keep]
        description = row[out_description].lower()

        if END_ROW.match(description):
            break

        if OPENING_ROW.match(description) or (not row[out_date] and PAGE_ROW.match(description)):
            continue

        if not row[out_date]:
            is_wrapped_text = row[out_description] and not any(
                cell for i, cell in enumerate(row) if i != out_description
            )

            if is_wrapped_text and len(output) > 1:
                previous = output[-1]
                previous[out_description] = f"{previous[out_description]} {row[out_description]}".strip()

            # A dateless row that is not wrapped text is a subtotal or
            # carried-forward balance, not a transaction.
            continue

        output.append(row)

    buffer = io.StringIO()
    csv.writer(buffer).writerows(output)
    return buffer.getvalue()


def _layout_tables(pages) -> list[Table]:
    """Rebuild a borderless table from where each word sits on the page.

    The header row fixes the columns: a word belongs to the last column whose
    header starts at or before it. Right-aligned amounts can start left of
    their header, so a number that reaches into a later column belongs there.
    A header split over two lines ("Value" / "Date") is joined, and on each
    page everything above the header (the bank's letterhead) is ignored.
    """
    tables: list[Table] = []
    columns: list[tuple[str, float]] | None = None

    for page in pages:
        lines = _lines(page.extract_words())
        rows: Table = []
        start = 0

        for index, line in enumerate(lines):
            header = _header_cells(line)

            if _is_header([name for name, _ in header]):
                columns = header
                names = [name for name, _ in columns]
                start = index + 1

                second = lines[index + 1] if index + 1 < len(lines) else []

                if (
                    second
                    and second[0]["top"] - line[0]["top"] < HEADER_LINE_GAP
                    and not any(ch.isdigit() for word in second for ch in word["text"])
                ):
                    for word in second:
                        column = _column_for(word, columns)
                        names[column] = f"{names[column]} {word['text']}"
                    start = index + 2

                rows.append(names)
                break

        if columns is None:
            continue

        for line in lines[start:]:
            cells = [""] * len(columns)

            for word in line:
                column = _column_for(word, columns)
                cells[column] = f"{cells[column]} {word['text']}".strip()

            rows.append(cells)

        if rows:
            tables.append(rows)

    return tables


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

    return [(_clean(text), x0) for text, x0, _ in cells]


def _column_for(word: dict, columns: list[tuple[str, float]]) -> int:
    starts = [x0 for _, x0 in columns]
    index = max((i for i, x0 in enumerate(starts) if x0 <= word["x0"] + 2), default=0)

    if NUMBER.match(word["text"]):
        index = max(
            (i for i, x0 in enumerate(starts) if x0 < word["x1"]),
            default=index,
        )

    return index


def _clean(cell: str | None) -> str:
    return " ".join((cell or "").split())


def _is_header(row: list[str]) -> bool:
    return looks_like_header(row)


def _column(names: list[str], kind: str) -> int:
    return next(i for i, name in enumerate(names) if classify_header(name) == kind)


def _open_error(exc: Exception, password: str | None) -> BadRequestError:
    # pdfplumber wraps pdfminer's PDFPasswordIncorrect, so look through the
    # whole exception chain and its arguments for a password error.
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
