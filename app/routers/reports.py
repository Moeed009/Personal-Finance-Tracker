from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dates import first_of_month
from app.core.security import CurrentUser
from app.schemas.report import MonthlyReport
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])
DbSession = Annotated[Session, Depends(get_db)]
MonthQuery = Annotated[date | None, Query(description="Any date inside the month; defaults to the current month")]


def _csv_response(content: str, filename: str) -> Response:
    return Response(content, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/monthly", response_model=MonthlyReport)
def monthly(user: CurrentUser, db: DbSession, month: MonthQuery = None):
    return report_service.monthly_report(db, user.id, month or date.today())

