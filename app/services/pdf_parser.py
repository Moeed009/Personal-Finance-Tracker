"""Turn a PDF bank statement into CSV text for the CSV parser.

The PDF's transaction table is extracted with pdfplumber and written out as
CSV, so PDF imports go through exactly the same parsing, validation,
duplicate detection and balance rules as CSV imports.
"""

import csv
import io
import re

from app.core.exceptions import BadRequestError
from app.services.csv_parser import ALIASES

Table = list[list[str | None]]

# Tables drawn with cell borders. Statements without borders are read from
# word positions instead (see _layout_tables).
RULED = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}

LINE_TOLERANCE = 3  # points: words this close vertically are on one line
HEADER_WORD_GAP = 6  # points: closer header words form one name ("Txn Date")
NUMBER = re.compile(r"^[+\-(]?(rs\.?|pkr)?\s?[\d,]+(\.\d+)?\)?(cr|dr)?$", re.IGNORECASE)


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
    description column) is found. Header rows repeated on later pages are
    dropped, and a description that wrapped onto its own line is joined back
    onto the row above it.
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

    output: list[list[str]] = [header]

    for row in rows[header_at + 1:]:
        if [cell.lower() for cell in row] == names:
            continue

        row = (row + [""] * len(header))[: len(header)]

        if (
            len(output) > 1
            and not row[date_col]
            and row[description_col]
            and not any(
                cell for i, cell in enumerate(row) if i != description_col
            )
        ):
            previous = output[-1]
            previous[description_col] = f"{previous[description_col]} {row[description_col]}".strip()
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
    """
    tables: list[Table] = []
    columns: list[tuple[str, float]] | None = None

    for page in pages:
        rows: Table = []

        for line in _lines(page.extract_words()):
            header = _header_cells(line)

            if _is_header([name for name, _ in header]):
                columns = header
                rows.append([name for name, _ in columns])
                continue

            if columns is None:
                continue

            cells = [""] * len(columns)

            for word in line:
                index = _column_for(word, columns)
                cells[index] = f"{cells[index]} {word['text']}".strip()

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
    cells = {cell.lower() for cell in row if cell}
    return bool(cells & set(ALIASES["date"])) and bool(cells & set(ALIASES["description"]))


def _column(names: list[str], kind: str) -> int:
    return next(i for i, name in enumerate(names) if name in ALIASES[kind])


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
