import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models.budget import BudgetStatus
from app.models.goal import Goal, GoalStatus
from app.schemas.goal import GoalUpdate
from app.services import goal_service
from app.services.budget_service import _exact_percent, status_for
from app.services.csv_parser import parse_amount


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Rs -300", Decimal("-300.00")),
        ("- PKR100.00", Decimal("-100.00")),
        ("300-", Decimal("-300.00")),
        ("1.234,56", Decimal("1234.56")),
        ("1,234,567.89", Decimal("1234567.89")),
        ("1.234.567", Decimal("1234567.00")),
        ("PKR36,200.98", Decimal("36200.98")),
        ("500.00 CR", Decimal("500.00")),
        ("12 345,67", Decimal("12345.67")),
        ("1,250", Decimal("1250.00")),
    ],
)
def test_bank_style_amounts(text, expected):
    assert parse_amount(text) == expected


def test_budget_just_under_the_limit_is_a_warning_not_exceeded():
    assert status_for(_exact_percent(Decimal("99.995"), Decimal("100"))) == BudgetStatus.WARNING
    assert status_for(_exact_percent(Decimal("100"), Decimal("100"))) == BudgetStatus.EXCEEDED


class _OneGoalDb:
    def __init__(self, goal):
        self.goal = goal

    def scalar(self, query):
        return self.goal

    def commit(self):
        pass


def _goal(saved: str, target: str, status: GoalStatus) -> Goal:
    return Goal(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Laptop",
        saved_amount=Decimal(saved),
        target_amount=Decimal(target),
        target_date=date.today() + timedelta(days=90),
        status=status,
    )


def test_raising_the_target_reopens_a_completed_goal():
    goal = _goal("1000", "1000", GoalStatus.COMPLETED)
    goal_service.update_goal(_OneGoalDb(goal), goal.user_id, goal.id, GoalUpdate(target_amount=Decimal("5000")))
    assert goal.status == GoalStatus.ACTIVE


def test_lowering_the_target_below_savings_completes_the_goal():
    goal = _goal("1000", "5000", GoalStatus.ACTIVE)
    goal_service.update_goal(_OneGoalDb(goal), goal.user_id, goal.id, GoalUpdate(target_amount=Decimal("800")))
    assert goal.status == GoalStatus.COMPLETED


def test_a_status_set_by_the_user_is_kept():
    goal = _goal("100", "5000", GoalStatus.ACTIVE)
    goal_service.update_goal(_OneGoalDb(goal), goal.user_id, goal.id, GoalUpdate(status=GoalStatus.COMPLETED))
    assert goal.status == GoalStatus.COMPLETED
