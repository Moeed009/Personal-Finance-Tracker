import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.schemas.goal import ContributionCreate, GoalCreate, GoalRead, GoalUpdate
from app.services import goal_service

router = APIRouter(prefix="/goals", tags=["Goals"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[GoalRead])
def list_goals(user: CurrentUser, db: DbSession):
    return goal_service.list_goals(db, user.id)


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(data: GoalCreate, user: CurrentUser, db: DbSession):
    return goal_service.create_goal(db, user.id, data)


@router.put("/{goal_id}", response_model=GoalRead)
def update_goal(goal_id: uuid.UUID, data: GoalUpdate, user: CurrentUser, db: DbSession):
    return goal_service.update_goal(db, user.id, goal_id, data)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: uuid.UUID, user: CurrentUser, db: DbSession):
    goal_service.delete_goal(db, user.id, goal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{goal_id}/contribute", response_model=GoalRead)
def contribute(goal_id: uuid.UUID, data: ContributionCreate, user: CurrentUser, db: DbSession):
    return goal_service.contribute(db, user.id, goal_id, data)
