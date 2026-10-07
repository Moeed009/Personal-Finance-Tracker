import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core import storage
from app.core.database import get_db
from app.core.security import CurrentUser
from app.schemas.common import Page
from app.schemas.imports import DownloadLink, ImportBatchRead, ImportedTransactionRead, ImportSummary
from app.services import import_service
from app.services.csv_parser import ColumnMapping

router = APIRouter(tags=["CSV Import"])
DbSession = Annotated[Session, Depends(get_db)]
DOWNLOAD_TTL = 300


@router.post("/transactions/import", response_model=ImportSummary, status_code=status.HTTP_201_CREATED)
def import_transactions(
    user: CurrentUser,
    db: DbSession,
    file: Annotated[UploadFile, File()],
    account_id: Annotated[uuid.UUID, Form()],
):
    return import_service.import_csv(db, user.id, account_id, file, ColumnMapping())


@router.get("/imports", response_model=list[ImportBatchRead])
def list_import_batches(user: CurrentUser, db: DbSession):
    return import_service.list_batches(db, user.id)



@router.get("/imports/{batch_id}/transactions", response_model=Page[ImportedTransactionRead])
def list_import_transactions(
    batch_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    items, total = import_service.list_batch_transactions(db, user.id, batch_id, page, page_size)
    return Page[ImportedTransactionRead](
        items=[ImportedTransactionRead.model_validate(i) for i in items], total=total, page=page, page_size=page_size
    )


@router.get("/imports/{batch_id}/download", response_model=DownloadLink)
def download_import_file(batch_id: uuid.UUID, user: CurrentUser, db: DbSession):
    batch = import_service.get_batch(db, user.id, batch_id)
    return DownloadLink(url=storage.create_signed_url(batch.storage_path, DOWNLOAD_TTL), expires_in=DOWNLOAD_TTL)