import logging
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from supabase_auth.errors import AuthApiError, AuthError

from app.core.exceptions import BadRequestError, ExternalServiceError, NotFoundError
from app.core.supabase import get_admin_client, get_auth_client
from app.models import Profile, User
from app.schemas.user import ProfileResponse, ProfileUpdateRequest

logger = logging.getLogger(__name__)


def _load(db: Session, user_id: uuid.UUID) -> tuple[User, Profile]:
    user = db.get(User, user_id)
    profile = db.scalar(
        select(Profile).where(Profile.user_id == user_id)
    )

    if user is None or profile is None:
        raise NotFoundError("Profile not found")

    return user, profile


def get_profile(db: Session, user_id: uuid.UUID) -> ProfileResponse:
    user, profile = _load(db, user_id)

    return ProfileResponse(
        id=profile.id,
        email=user.email,
        full_name=user.full_name,
        currency=profile.currency,
    )


def update_profile(
    db: Session,
    user_id: uuid.UUID,
    data: ProfileUpdateRequest,
) -> ProfileResponse:
    user, profile = _load(db, user_id)

    user.full_name = data.full_name
    profile.currency = data.currency

    db.commit()

    return ProfileResponse(
        email=user.email,
        full_name=user.full_name,
        currency=profile.currency,
    )


def _verify_password(email: str, password: str) -> None:
    try:
        get_auth_client().auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except AuthApiError as exc:
        logger.warning("Password verification failed for %s", email)
        raise BadRequestError("Incorrect password") from exc
    except AuthError as exc:
        logger.warning(
            "Supabase authentication error during password verification"
        )
        raise ExternalServiceError(
            "Authentication service error"
        ) from exc
    except httpx.HTTPError as exc:
        logger.exception("Supabase password verification failed")
        raise ExternalServiceError(
            "Authentication service unavailable"
        ) from exc


def _remove_auth_user(user_id: uuid.UUID) -> None:
    admin = get_admin_client().auth.admin

    try:
        admin.delete_user(str(user_id))
        logger.info("Supabase Auth user %s deleted", user_id)
        return

    except AuthApiError as exc:
        if getattr(exc, "status", None) == 404:
            logger.info(
                "Supabase Auth user %s was already deleted",
                user_id,
            )
            return
        raise

    except httpx.HTTPError as exc:
        logger.warning(
            "Supabase Auth delete request failed for %s. "
            "Checking whether the user was actually deleted.",
            user_id,
        )

        try:
            admin.get_user_by_id(str(user_id))
        except AuthApiError as check_exc:
            if getattr(check_exc, "status", None) == 404:
                logger.info(
                    "Supabase Auth user %s was deleted "
                    "despite the previous request failure",
                    user_id,
                )
                return
            raise
        except httpx.HTTPError:
            logger.exception(
                "Could not verify Supabase Auth user %s",
                user_id,
            )
            raise exc

        raise exc

def delete_profile(
    db: Session,
    user_id: uuid.UUID,
    password: str,
) -> None:
    user, _ = _load(db, user_id)

    _verify_password(user.email, password)
    _remove_auth_user(user_id)

    try:
        db.delete(user)
        db.commit()
        logger.info(
            "Local account %s deleted successfully",
            user_id,
        )

    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed to delete local account %s "
            "after Supabase Auth deletion",
            user_id,
        )
        raise ExternalServiceError(
            "Could not delete account"
        ) from exc
