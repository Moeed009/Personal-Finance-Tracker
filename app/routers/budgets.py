import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate
from app.services import budget_service

router = APIRouter(prefix="/budgets", tags=["Budgets"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[BudgetRead])
def list_budgets(user: CurrentUser, db: DbSession, month: date | None = None):
    return budget_service.list_budgets(db, user.id, month)


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(data: BudgetCreate, user: CurrentUser, db: DbSession):
    return budget_service.create_budget(db, user.id, data)


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(budget_id: uuid.UUID, data: BudgetUpdate, user: CurrentUser, db: DbSession):
    return budget_service.update_budget(db, user.id, budget_id, data)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: uuid.UUID, user: CurrentUser, db: DbSession):
    budget_service.delete_budget(db, user.id, budget_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
