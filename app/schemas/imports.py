import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel
from app.schemas.transaction import TransactionRead


class RowError(BaseModel):
    row: int
    message: str


class ImportSummary(BaseModel):
    batch_id: uuid.UUID
    filename: str
    rows_total: int
    rows_imported: int
    rows_skipped: int
    rows_failed: int
    errors: list[RowError]


class ImportBatchRead(ORMModel):
    id: uuid.UUID
    account_id: uuid.UUID
    filename: str
    file_size: int
    rows_total: int
    rows_imported: int
    rows_skipped: int
    rows_failed: int
    created_at: datetime


class DownloadLink(BaseModel):
    url: str
    expires_in: int


class ImportedTransactionRead(TransactionRead):
    dedupe_hash: str | None
    raw_data: dict | None