from pathlib import Path
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import get_session_factory
from app.models.category import Category
from app.models.category import CategoryType


DEFAULT_CATEGORIES: list[tuple[str, CategoryType]] = [
    *((name, CategoryType.EXPENSE) for name in (
        "Food",
        "Transport",
        "Bills",
        "Shopping",
        "Health",
        "Entertainment",
        "Education",
        "Housing",
        "Personal Care",
        "Family",
        "Charity",
        "Taxes",
        "Insurance",
    )),
    *((name, CategoryType.INCOME) for name in (
        "Salary",
        "Freelance Income",
        "Business Income",
        "Investment Income",
        "Gifts Received",
        "Other Income",
    )),
    ("Uncategorized", CategoryType.BOTH),
]


def seed_default_categories(db: Session) -> int:
    existing = set(
        db.scalars(
            select(Category.name).where(
                Category.is_default.is_(True)
            )
        )
    )

    created = 0

    for name, category_type in DEFAULT_CATEGORIES:
        if name not in existing:
            db.add(
                Category(
                    name=name,
                    type=category_type,
                    is_default=True,
                    user_id=None,
                )
            )
            created += 1

    db.commit()

    return created


def main() -> None:
    session_factory = get_session_factory()

    with session_factory() as db:
        created = seed_default_categories(db)
        print(f"Default categories created: {created}")


if __name__ == "__main__":
    main()
