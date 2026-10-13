import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.schemas.alert import AlertRead
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])
DbSession = Annotated[Session, Depends(get_db)]


class MarkedRead(BaseModel):
    updated: int


@router.get("", response_model=list[AlertRead])
def list_alerts(user: CurrentUser, db: DbSession, unread_only: bool = False):
    return alert_service.list_alerts(db, user.id, unread_only)


@router.post("/read-all", response_model=MarkedRead)
def mark_all_alerts_read(user: CurrentUser, db: DbSession):
    return MarkedRead(updated=alert_service.mark_all_read(db, user.id))


@router.patch("/{alert_id}/read", response_model=AlertRead)
def mark_alert_read(alert_id: uuid.UUID, user: CurrentUser, db: DbSession):
    return alert_service.mark_read(db, user.id, alert_id)
