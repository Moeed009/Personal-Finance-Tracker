import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.schemas.alert import AlertRead
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[AlertRead])
def list_alerts(user: CurrentUser, db: DbSession, ):
    return alert_service.list_alerts(db, user.id, )


