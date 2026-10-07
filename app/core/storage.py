import logging

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.core.supabase import get_admin_client
import uuid
logger = logging.getLogger(__name__)


def _bucket():
    return get_admin_client().storage.from_(get_settings().import_bucket_name)


def upload_csv(path: str, content: bytes) -> None:
    try:
        _bucket().upload(path, content, {"content-type": "text/csv", "upsert": "false"})
    except Exception as exc:
        logger.exception("CSV upload failed")
        raise ExternalServiceError("Could not store the uploaded file") from exc


def remove_files(paths: list[str]) -> None:
    if not paths:
        return
    try:
        _bucket().remove(paths)
    except Exception:
        logger.warning("Could not remove %d file(s) from storage", len(paths), exc_info=True)


def create_signed_url(path: str, expires_in: int = 300) -> str:
    try:
        result = _bucket().create_signed_url(path, expires_in)
    except Exception as exc:
        raise ExternalServiceError("Could not create a download link") from exc
    return result.get("signedURL") or result.get("signedUrl") or ""

def remove_user_files(user_id: uuid.UUID) -> None:
    folder = str(user_id)
    bucket = _bucket()

    try:
        for _ in range(100):
            items = bucket.list(folder, {"limit": 100})
            paths = [f"{folder}/{item['name']}" for item in items if item.get("name")]

            if not paths:
                return

            bucket.remove(paths)
    except Exception as exc:
        logger.exception("Could not remove stored files for user %s", user_id)
        raise ExternalServiceError("Could not remove stored files") from exc