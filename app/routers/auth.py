from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.exceptions import AuthenticationError
from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.database import get_db
from app.core.security import CurrentUser, bearer_scheme, extract_token
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    response: Response,
    db: DbSession,
):
    user, session = auth_service.register(db, data)

    if session is None:
        raise AuthenticationError(
            "Account created, but authentication session was not created"
        )

    set_auth_cookies(
        response,
        session.access_token,
        session.refresh_token,
    )

    return TokenResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        access_token=session.access_token,
        expires_in=session.expires_in,
    )
    
@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    response: Response,
    db: DbSession,
):
    session, user = auth_service.login(db, data)

    set_auth_cookies(
        response,
        session.access_token,
        session.refresh_token,
    )

    return TokenResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
        access_token=session.access_token,
        expires_in=session.expires_in,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: Request,
    response: Response,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
):
    token = extract_token(request, credentials)

    if token:
        auth_service.revoke_session(token)

    clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT

    return response


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(data: ForgotPasswordRequest):
    auth_service.request_password_reset(data.email)
    return MessageResponse(
        message="If an account exists for this email, a reset link has been sent"
    )

@router.post("/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPasswordRequest):
    if data.token_hash:
        auth_service.reset_password(data.token_hash, data.new_password)
    else:
        auth_service.reset_password_with_session(
            data.access_token or "",
            data.refresh_token or "",
            data.new_password,
        )
    return MessageResponse(message="Your password has been updated. You can now log in")
