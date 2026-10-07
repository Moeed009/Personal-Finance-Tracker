import logging
import uuid

from app.core.config import get_settings
from app.core.supabase import get_admin_client

logger = logging.getLogger(__name__)


class ImportStorageError(RuntimeError):
    pass


def build_storage_path(user_id: uuid.UUID, batch_id: uuid.UUID) -> str:
    return f"{user_id}/{batch_id}.csv"


def _bucket():
    return get_admin_client().storage.from_(get_settings().import_bucket_name)


def upload_csv(user_id: uuid.UUID, batch_id: uuid.UUID, content: bytes) -> str:
    path = build_storage_path(user_id, batch_id)
    try:
        _bucket().upload(
            path,
            content,
            {"content-type": "text/csv", "upsert": "false"},
        )
    except Exception as exc:
        logger.exception("CSV upload failed for path %s", path)
        raise ImportStorageError("Could not store the uploaded file") from exc
    return path


def delete_files(paths: list[str]) -> None:
    if not paths:
        return

    try:
        result = _bucket().remove(paths)
        logger.info("CSV delete result: %s", result)
        print("delete result:", result)
    except Exception as exc:
        logger.exception("CSV delete failed for %d file(s)", len(paths))
        raise ImportStorageError("Could not delete stored files") from exc

def check_bucket() -> bool:
    bucket_name = get_settings().import_bucket_name

    try:
        buckets = get_admin_client().storage.list_buckets()

        return any(bucket.name == bucket_name for bucket in buckets)

    except Exception as exc:
        logger.exception("Storage bucket check failed")
        raise ImportStorageError(
            "Could not access Supabase Storage"
        ) from exc