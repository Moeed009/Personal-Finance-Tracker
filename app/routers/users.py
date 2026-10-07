from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.cookies import clear_auth_cookies
from app.core.database import get_db
from app.core.security import CurrentUser
from app.schemas.user import UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=UserRead)
def get_profile(user: CurrentUser):
    return UserRead.from_user(user)


@router.patch("", response_model=UserRead)
def update_profile(
    data: UserUpdate,
    user: CurrentUser,
    db: DbSession,
):
    return UserRead.from_user(
        user_service.update_user(db, user, data)
    )

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(user: CurrentUser, db: DbSession):
    user_service.delete_user(db, user.id)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_auth_cookies(response)
    return response
