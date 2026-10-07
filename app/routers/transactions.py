import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.schemas.common import Page
from app.schemas.transaction import (
    TransactionCreate,
    TransactionFilters,
    TransactionRead,
    TransactionUpdate,
    TransferCreate,
    TransferRead,
)
from app.services import transaction_service

router = APIRouter(tags=["Transactions"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/transactions", response_model=Page[TransactionRead])
def list_transactions(filters: Annotated[TransactionFilters, Query()], user: CurrentUser, db: DbSession):
    items, total = transaction_service.list_transactions(db, user.id, filters)
    return Page[TransactionRead](
        items=[TransactionRead.model_validate(i) for i in items], total=total,
        page=filters.page, page_size=filters.page_size,
    )


@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(data: TransactionCreate, user: CurrentUser, db: DbSession):
    return transaction_service.create_transaction(db, user.id, data)


@router.patch("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: uuid.UUID, data: TransactionUpdate, user: CurrentUser, db: DbSession):
    return transaction_service.update_transaction(db, user.id, transaction_id, data)


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: uuid.UUID, user: CurrentUser, db: DbSession):
    transaction_service.delete_transaction(db, user.id, transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/transfers", response_model=TransferRead, status_code=status.HTTP_201_CREATED)
def create_transfer(data: TransferCreate, user: CurrentUser, db: DbSession):
    group_id, outgoing, incoming = transaction_service.create_transfer(db, user.id, data)
    return TransferRead(
        transfer_group_id=group_id,
        outgoing=TransactionRead.model_validate(outgoing),
        incoming=TransactionRead.model_validate(incoming),
    )
