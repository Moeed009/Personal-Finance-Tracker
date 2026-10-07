import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.schemas.account import (
    AccountBalanceSummary,
    AccountCreate,
    AccountRead,
    AccountSummary,
    AccountUpdate,
)
from app.services import account_service

router = APIRouter(prefix="/accounts", tags=["Accounts"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[AccountRead])
def list_accounts(user: CurrentUser, db: DbSession):
    return account_service.list_accounts(db, user.id)


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(data: AccountCreate, user: CurrentUser, db: DbSession):
    return account_service.create_account(db, user.id, data)


@router.get("/summary", response_model=AccountSummary)
def account_summary(user: CurrentUser, db: DbSession):
    accounts, total = account_service.summary(db, user.id)
    return AccountSummary(accounts=accounts, total_balance=total)


@router.get("/{account_id}/summary", response_model=AccountBalanceSummary)
def account_balance_summary(account_id: uuid.UUID, user: CurrentUser, db: DbSession):
    return account_service.get_account_summary(db, user.id, account_id)


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(account_id: uuid.UUID, data: AccountUpdate, user: CurrentUser, db: DbSession):
    return account_service.update_account(db, user.id, account_id, data)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: uuid.UUID, user: CurrentUser, db: DbSession, force: bool = False):
    account_service.delete_account(db, user.id, account_id, force)
    return Response(status_code=status.HTTP_204_NO_CONTENT)