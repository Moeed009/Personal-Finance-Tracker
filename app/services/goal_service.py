import math
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.money import ZERO, money, percent
from app.models.goal import GoalStatus
from app.models.goal import Goal
from app.schemas.goal import ContributionCreate, GoalCreate, GoalRead, GoalUpdate


def to_read(goal: Goal, today: date | None = None) -> GoalRead:
    today = today or date.today()
    remaining = max(goal.target_amount - goal.saved_amount, ZERO)
    if goal.status == GoalStatus.COMPLETED or remaining == 0:
        monthly = ZERO
    else:
        months_left = max(1, math.ceil((goal.target_date - today).days / 30))
        monthly = money(remaining / months_left)
    return GoalRead(
        id=goal.id, name=goal.name, target_amount=goal.target_amount, saved_amount=goal.saved_amount,
        target_date=goal.target_date, status=goal.status,
        progress_percent=min(percent(goal.saved_amount, goal.target_amount), money(100)),
        remaining_amount=money(remaining), required_monthly_saving=monthly,
    )


def _get(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> Goal:
    goal = db.scalar(select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id))
    if goal is None:
        raise NotFoundError("Goal not found")
    return goal


def list_goals(db: Session, user_id: uuid.UUID) -> list[GoalRead]:
    goals = db.scalars(select(Goal).where(Goal.user_id == user_id).order_by(Goal.target_date))
    return [to_read(g) for g in goals]


def create_goal(db: Session, user_id: uuid.UUID, data: GoalCreate) -> GoalRead:
    if data.target_date < date.today():
        raise BadRequestError("Target date cannot be in the past")
    goal = Goal(user_id=user_id, name=data.name.strip(), target_amount=data.target_amount, target_date=data.target_date,
                saved_amount=ZERO, status=GoalStatus.ACTIVE)
    db.add(goal)
    db.commit()
    return to_read(goal)


def update_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID, data: GoalUpdate) -> GoalRead:
    goal = _get(db, user_id, goal_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(goal, field, value)
    db.commit()
    return to_read(goal)


def delete_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
    db.delete(_get(db, user_id, goal_id))
    db.commit()


def contribute(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID, data: ContributionCreate) -> GoalRead:
    goal = _get(db, user_id, goal_id)
    if goal.status == GoalStatus.COMPLETED:
        raise BadRequestError("Goal is already completed")
    goal.saved_amount = goal.saved_amount + data.amount
    if goal.saved_amount >= goal.target_amount:
        goal.status = GoalStatus.COMPLETED
    db.commit()
    return to_read(goal)
