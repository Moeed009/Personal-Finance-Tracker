import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["Categories"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[CategoryRead])
def list_categories(user: CurrentUser, db: DbSession):
    return category_service.list_categories(db, user.id)


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, user: CurrentUser, db: DbSession):
    return category_service.create_category(db, user.id, data)


@router.patch("/{category_id}", response_model=CategoryRead)
def rename_category(category_id: uuid.UUID, data: CategoryUpdate, user: CurrentUser, db: DbSession):
    return category_service.rename_category(db, user.id, category_id, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: uuid.UUID, user: CurrentUser, db: DbSession):
    category_service.deactivate_category(db, user.id, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
