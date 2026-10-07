import logging
import uuid
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select
from sqlalchemy.orm import Session
from supabase import AuthApiError

from app.core import storage
from app.core.config import get_settings
from app.core.database import get_session_factory
from app.core.supabase import get_admin_client
from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.exceptions import AuthenticationError, BadRequestError, ExternalServiceError
from app.core.supabase import get_anon_client
from supabase import AuthApiError, AuthError
logger = logging.getLogger(__name__)


def update_user(
    db: Session,
    user: User,
    data: UserUpdate,
) -> User:
    if data.full_name is not None:
        user.full_name = data.full_name.strip()

    if data.currency is not None:
        user.profile.currency = data.currency

    if data.new_password is not None:
        if data.current_password is None:
            raise BadRequestError(
                "Current password is required to change password"
            )

        try:
            client = get_anon_client()

            result = client.auth.sign_in_with_password(
                {
                    "email": user.email,
                    "password": data.current_password,
                }
            )

            if result.user is None or result.session is None:
                raise AuthenticationError(
                    "Current password is incorrect"
                )

            client.auth.update_user(
                {
                    "password": data.new_password,
                }
            )

        except AuthApiError as exc:
            raise AuthenticationError(
                "Current password is incorrect"
            ) from exc
        except AuthError as exc:
            raise ExternalServiceError(
                "Authentication service error"
            ) from exc

    elif data.current_password is not None:
        raise BadRequestError(
            "New password is required when current password is provided"
        )

    db.commit()
    db.refresh(user)

    return user


def delete_user(
    db: Session,
    user_id: uuid.UUID,
) -> None:
    user = db.get(User, user_id)

    if user is None:
        return

    if user.deleted_at is not None:
        return

    user.deleted_at = datetime.now(timezone.utc)

    db.commit()


def _delete_auth_user(user_id: uuid.UUID) -> None:
    try:
        get_admin_client().auth.admin.delete_user(str(user_id))
    except AuthApiError as exc:
        if getattr(exc, "status", None) == 404:
            logger.info("Auth user %s already removed", user_id)
            return
        raise


def purge_expired_users(db: Session) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(
        hours=get_settings().account_deletion_grace_hours
    )

    expired_ids = list(
        db.scalars(
            select(User.id).where(
                User.deleted_at.is_not(None),
                User.deleted_at <= cutoff,
            )
        )
    )

    purged = 0

    for user_id in expired_ids:
        try:
            storage.remove_user_files(user_id)
            _delete_auth_user(user_id)

            user = db.get(User, user_id)
            if user is not None:
                db.delete(user)
            db.commit()

            purged += 1
        except Exception:
            db.rollback()
            logger.exception("Failed to purge user %s", user_id)

    if purged:
        logger.info("Purged %d expired user(s)", purged)

    return purged


def _run_purge() -> None:
    db = get_session_factory()()
    try:
        purge_expired_users(db)
    except Exception:
        logger.exception("User purge job crashed")
    finally:
        db.close()


def create_purge_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _run_purge,
        trigger="interval",
        minutes=get_settings().purge_interval_minutes,
        id="purge_expired_users",
        max_instances=1,
        coalesce=True,
    )
    return scheduler