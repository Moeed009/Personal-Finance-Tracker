import uuid
from datetime import datetime

from app.models.alert import AlertType
from app.schemas.common import ORMModel


class AlertRead(ORMModel):
    id: uuid.UUID
    alert_type: AlertType
    message: str
    is_read: bool
    created_at: datetime
