import hashlib
import logging
import uuid
from datetime import date
from decimal import Decimal

from fastapi import UploadFile
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import storage
from app.core.config import get_settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    PayloadTooLargeError,
)
from app.core.money import money
from app.models.account import Account
from app.models.import_batch import ImportBatch
from app.models.transaction import Transaction, TransactionType
from app.schemas.imports import ImportSummary, RowError
from app.services import account_service, own_transfers
from app.services.categorization import CategoryResolver, derive_merchant, normalize
from app.services.pdf_parser import pdf_to_csv_text
from app.services.csv_parser import (
    ColumnMapping,
    ParsedRow,
    decode_content,
    parse_csv,
)

logger = logging.getLogger(__name__)

CHUNK = 500


def compute_dedupe_hash(
    account_id: uuid.UUID,
    txn_date: date,
    amount,
    description: str,
) -> str:
    key = f"{account_id}|{txn_date.isoformat()}|{amount:.2f}|{normalize(description)}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _existing_hashes(
    db: Session,
    account_id: uuid.UUID,
    hashes: list[str],
) -> set[str]:
    found: set[str] = set()

    for start in range(0, len(hashes), CHUNK):
        chunk = hashes[start:start + CHUNK]
        found.update(
            db.scalars(
                select(Transaction.dedupe_hash).where(
                    Transaction.account_id == account_id,
                    Transaction.dedupe_hash.in_(chunk),
                )
            )
        )

    return found


def _statement_opening_balance(
    db: Session,
    account: Account,
    rows: list[ParsedRow],
) -> Decimal | None:
    if not rows:
        return None

    newest_first = (
        len(rows) > 1
        and rows[0].transaction_date > rows[-1].transaction_date
    )

    closing = rows[0] if newest_first else rows[-1]

    if closing.balance is None:
        return None

    signed = case(
        (
            Transaction.type == TransactionType.INCOME,
            Transaction.amount,
        ),
        (
            Transaction.type == TransactionType.EXPENSE,
            -Transaction.amount,
        ),
        else_=0,
    )

    net = db.scalar(
        select(func.coalesce(func.sum(signed), 0)).where(
            Transaction.account_id == account.id,
            Transaction.transaction_date <= closing.transaction_date,
        )
    )

    return money(closing.balance - money(net))


def read_upload(file: UploadFile) -> bytes:
    filename = (file.filename or "").lower()

    if not filename.endswith((".csv", ".pdf")):
        raise BadRequestError("Only .csv and .pdf files are accepted")

    limit = get_settings().max_upload_size_mb * 1024 * 1024

    content = file.file.read(limit + 1)

    if len(content) > limit:
        raise PayloadTooLargeError(
            f"File exceeds the {get_settings().max_upload_size_mb} MB limit"
        )

    if not content.strip():
        raise BadRequestError("The uploaded file is empty")

    if filename.endswith(".pdf") and not content.lstrip().startswith(b"%PDF"):
        raise BadRequestError("The file is not a valid PDF")

    return content


def import_csv(
    db: Session,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    file: UploadFile,
    mapping: ColumnMapping,
    password: str | None = None,
) -> ImportSummary:
    account = account_service.get_account(db, user_id, account_id)

    content = read_upload(file)
    is_pdf = (file.filename or "").lower().endswith(".pdf")

    if is_pdf:
        try:
            parsed = parse_csv(pdf_to_csv_text(content, password), mapping)
        except BadRequestError as exc:
            if exc.message.startswith("CSV must contain"):
                raise BadRequestError(
                    "The table in this PDF needs a date, a description and an amount column"
                ) from exc
            raise
    else:
        parsed = parse_csv(
            decode_content(content),
            mapping,
        )

    extension = "pdf" if is_pdf else "csv"

    batch = ImportBatch(
        id=uuid.uuid4(),
        user_id=user_id,
        account_id=account.id,
        filename=(file.filename or f"import.{extension}")[:255],
        storage_path=f"{user_id}/{uuid.uuid4()}.{extension}",
        file_size=len(content),
        rows_total=parsed.total,
    )

    storage.upload_csv(
        batch.storage_path,
        content,
        "application/pdf" if is_pdf else "text/csv",
    )

    try:
        hashes = {
            row.row: compute_dedupe_hash(
                account.id,
                row.transaction_date,
                row.amount,
                row.description,
            )
            for row in parsed.rows
        }

        seen = _existing_hashes(
            db,
            account.id,
            list(hashes.values()),
        )

        resolver = CategoryResolver(db, user_id)

        db.add(batch)
        db.flush()

        imported: list[Transaction] = []
        skipped = parsed.skipped

        for row in parsed.rows:
            digest = hashes[row.row]

            if digest in seen:
                skipped += 1
                continue

            seen.add(digest)

            imported.append(
                Transaction(
                    user_id=user_id,
                    account_id=account.id,
                    import_batch_id=batch.id,
                    category_id=resolver.resolve(
                        row.description,
                        row.type,
                    ),
                    type=row.type,
                    amount=row.amount,
                    description=row.description,
                    merchant=derive_merchant(row.description),
                    transaction_date=row.transaction_date,
                    dedupe_hash=digest,
                    raw_data=row.raw,
                )
            )

        db.add_all(imported)

        batch.rows_imported = len(imported)
        batch.rows_skipped = skipped
        batch.rows_failed = len(parsed.errors)

        db.flush()

        opening_balance = _statement_opening_balance(
            db,
            account,
            parsed.rows,
        )

        if opening_balance is not None:
            account.opening_balance = opening_balance

        db.commit()

    except IntegrityError:
        logger.exception("CSV import failed with an integrity error")
        db.rollback()
        storage.remove_files([batch.storage_path])
        raise ConflictError(
            "Import conflicted with existing data, please retry"
        )

    except Exception:
        db.rollback()
        storage.remove_files([batch.storage_path])
        raise

    # Moves between the user's own accounts are transfers, not income or
    # spending. The import is already saved, so a failure here only logs.
    try:
        own_transfers.mark_own_transfers(db, user_id)
    except Exception:
        db.rollback()
        logger.exception("Could not mark own transfers after import")

    return ImportSummary(
        batch_id=batch.id,
        filename=batch.filename,
        rows_total=batch.rows_total,
        rows_imported=batch.rows_imported,
        rows_skipped=batch.rows_skipped,
        rows_failed=batch.rows_failed,
        errors=[
            RowError(row=row, message=message)
            for row, message in parsed.errors
        ],
    )


def list_batches(
    db: Session,
    user_id: uuid.UUID,
) -> list[ImportBatch]:
    return list(
        db.scalars(
            select(ImportBatch)
            .where(ImportBatch.user_id == user_id)
            .order_by(ImportBatch.created_at.desc())
        )
    )


def get_batch(
    db: Session,
    user_id: uuid.UUID,
    batch_id: uuid.UUID,
) -> ImportBatch:
    batch = db.scalar(
        select(ImportBatch).where(
            ImportBatch.id == batch_id,
            ImportBatch.user_id == user_id,
        )
    )

    if batch is None:
        raise NotFoundError("Import batch not found")

    return batch


def list_batch_transactions(
    db: Session,
    user_id: uuid.UUID,
    batch_id: uuid.UUID,
    page: int,
    page_size: int,
) -> tuple[list[Transaction], int]:
    batch = get_batch(
        db,
        user_id,
        batch_id,
    )

    query = select(Transaction).where(
        Transaction.import_batch_id == batch.id,
        Transaction.user_id == user_id,
    )

    total = (
        db.scalar(
            select(func.count())
            .select_from(query.subquery())
        )
        or 0
    )

    items = db.scalars(
        query
        .order_by(
            Transaction.transaction_date,
            Transaction.description,
            Transaction.id,
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return list(items), total
