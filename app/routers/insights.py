from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dates import month_bounds
from app.core.exceptions import BadRequestError
from app.core.security import CurrentUser
from app.schemas.insight import (
    CategorySpend,
    InsightMessage,
    PeriodSummary,
    TopResult,
    TrendPoint,
    UnusualItem,
)
from app.services import insight_service

router = APIRouter(prefix="/insights", tags=["Insights"])
DbSession = Annotated[Session, Depends(get_db)]


def _period(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    start, end = month_bounds(date.today())
    start, end = date_from or start, date_to or end
    if start > end:
        raise BadRequestError("date_from must not be after date_to")
    return start, end


@router.get("/summary", response_model=PeriodSummary)
def summary(user: CurrentUser, db: DbSession, date_from: date | None = None, date_to: date | None = None):
    return insight_service.period_summary(db, user.id, *_period(date_from, date_to))


@router.get("/categories", response_model=list[CategorySpend])
def categories(user: CurrentUser, db: DbSession, date_from: date | None = None, date_to: date | None = None):
    return insight_service.spending_by_category(db, user.id, *_period(date_from, date_to))


@router.get("/trends", response_model=list[TrendPoint])
def trends(user: CurrentUser, db: DbSession, months: Annotated[int, Query(ge=1, le=24)] = 6):
    return insight_service.trends(db, user.id, months)






@router.get("/unusual", response_model=list[UnusualItem])
def unusual(user: CurrentUser, db: DbSession, month: date | None = None):
    return insight_service.detect_unusual(db, user.id, month)
