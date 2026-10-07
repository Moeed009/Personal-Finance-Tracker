import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from supabase import AuthApiError, AuthError

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    ExternalServiceError,
    TooManyRequestsError,
)
from app.core.supabase import get_admin_client, get_anon_client
from app.models.user import Profile, User
from app.schemas.auth import LoginRequest, RegisterRequest

logger = logging.getLogger(__name__)


def register(
    db: Session,
    data: RegisterRequest,
):
    email = data.email.lower()

    if db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise ConflictError("Email is already registered")

    try:
        result = get_anon_client().auth.sign_up(
            {
                "email": email,
                "password": data.password,
                "options": {
                    "data": {
                        "full_name": data.full_name,
                    }
                },
            }
        )
    except AuthApiError as exc:
        raise BadRequestError(exc.message) from exc
    except AuthError as exc:
        raise ExternalServiceError("Authentication service error") from exc

    supabase_user = result.user

    if supabase_user is None:
        raise ExternalServiceError(
            "Authentication service returned no user"
        )

    if getattr(supabase_user, "identities", None) == []:
        raise ConflictError("Email is already registered")

    user = User(
        id=uuid.UUID(str(supabase_user.id)),
        email=email,
        full_name=data.full_name,
    )
    user.profile = Profile(currency=get_settings().default_currency)

    try:
        db.add(user)
        db.commit()
    except Exception:
        db.rollback()
        _delete_auth_user(str(supabase_user.id))
        raise

    return user, result.session

def login(db: Session, data: LoginRequest):
    try:
        result = get_anon_client().auth.sign_in_with_password(
            {
                "email": data.email.lower(),
                "password": data.password,
            }
        )
    except AuthApiError as exc:
        raise AuthenticationError(
            "Invalid email or password"
        ) from exc
    except AuthError as exc:
        raise ExternalServiceError(
            "Authentication service error"
        ) from exc

    session = result.session

    if session is None or result.user is None:
        raise AuthenticationError("Invalid email or password")

    user_id = uuid.UUID(str(result.user.id))

    user = db.get(User, user_id)

    if user is None:
        raise AuthenticationError("User profile not found")

    if user.deleted_at is not None:
        now = datetime.now(timezone.utc)
        restore_deadline = user.deleted_at + timedelta(
            hours=get_settings().account_deletion_grace_hours
        )

        if now > restore_deadline:
            revoke_session(session.access_token)
            raise AuthenticationError(
                "Account deletion window has expired"
            )

        user.deleted_at = None
        db.commit()

    return session, user


def revoke_session(access_token: str) -> None:
    try:
        get_admin_client().auth.admin.sign_out(access_token, "local")
    except Exception:
        logger.warning(
            "Could not revoke Supabase session",
            exc_info=True,
        )


def _delete_auth_user(user_id: str) -> None:
    try:
        get_admin_client().auth.admin.delete_user(user_id)
    except Exception:
        logger.error(
            "Could not delete Supabase auth user %s",
            user_id,
            exc_info=True,
        )


def delete_auth_user(user_id: uuid.UUID) -> None:
    try:
        get_admin_client().auth.admin.delete_user(str(user_id))
    except Exception as exc:
        raise ExternalServiceError(
            "Could not delete the authentication account"
        ) from exc

    

RESET_LINK_INVALID = "This reset link is invalid or has expired. Please request a new one"


def request_password_reset(email: str) -> None:
    redirect_to = f"{get_settings().frontend_url.rstrip('/')}/reset-password"

    try:
        get_anon_client().auth.reset_password_for_email(
            email.lower(),
            {"redirect_to": redirect_to},
        )
    except AuthApiError as exc:
        if exc.status == 429:
            raise TooManyRequestsError(
                "Please wait a minute before requesting another reset email"
            ) from exc
        logger.error("Password reset email failed: %s", exc.message)
    except AuthError:
        logger.error("Password reset email failed", exc_info=True)


def reset_password(access_token: str, new_password: str) -> None:
    try:
        user_response = get_anon_client().auth.get_user(access_token)
    except AuthApiError as exc:
        raise BadRequestError(RESET_LINK_INVALID) from exc
    except AuthError as exc:
        raise ExternalServiceError("Authentication service error") from exc

    user = user_response.user

    if user is None:
        raise BadRequestError(RESET_LINK_INVALID)

    try:
        get_admin_client().auth.admin.update_user_by_id(
            str(user.id),
            {"password": new_password},
        )
    except AuthApiError as exc:
        raise BadRequestError(exc.message) from exc
    except AuthError as exc:
        raise ExternalServiceError("Authentication service error") from exc

    try:
        get_admin_client().auth.admin.sign_out(access_token, "global")
    except Exception:
        logger.warning(
            "Could not revoke sessions after password reset",
            exc_info=True,
        )



def reset_password_with_session(
    access_token: str, refresh_token: str, new_password: str
) -> None:
    client = get_anon_client()

    try:
        client.auth.set_session(access_token, refresh_token)
    except AuthError as exc:
        raise BadRequestError(RESET_LINK_INVALID) from exc

    try:
        client.auth.update_user({"password": new_password})
    except AuthApiError as exc:
        raise BadRequestError(exc.message) from exc
    except AuthError as exc:
        raise ExternalServiceError("Authentication service error") from exc

    try:
        get_admin_client().auth.admin.sign_out(access_token, "global")
    except Exception:
        logger.warning("Could not revoke sessions after password reset", exc_info=True)