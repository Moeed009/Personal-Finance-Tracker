import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.category import Category
from app.models.category import CategoryType
from app.models.transaction import TransactionType

from app.schemas.category import CategoryCreate, CategoryUpdate


def _visible(user_id: uuid.UUID):
    return select(Category).where(
        or_(Category.user_id == user_id, Category.is_default.is_(True)), Category.is_active.is_(True)
    )


def list_categories(db: Session, user_id: uuid.UUID) -> list[Category]:
    return list(db.scalars(_visible(user_id).order_by(Category.is_default.desc(), Category.name)))


def get_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    category = db.scalar(_visible(user_id).where(Category.id == category_id))
    if category is None:
        raise NotFoundError("Category not found")
    return category


def get_uncategorized(db: Session) -> Category:
    category = db.scalar(select(Category).where(Category.is_default.is_(True), Category.name == "Uncategorized"))
    if category is None:
        raise BadRequestError("Default categories are not seeded")
    return category


def ensure_compatible(category: Category, transaction_type: TransactionType) -> None:
    if category.type == CategoryType.BOTH:
        return
    if category.type.value != transaction_type.value:
        raise BadRequestError(f"Category '{category.name}' cannot be used for {transaction_type.value} transactions")


def _ensure_unique_name(db: Session, user_id: uuid.UUID, name: str, exclude_id: uuid.UUID | None = None) -> None:
    query = _visible(user_id).where(func.lower(Category.name) == name.lower())
    if exclude_id:
        query = query.where(Category.id != exclude_id)
    if db.scalar(query) is not None:
        raise ConflictError("A category with this name already exists")


def create_category(db: Session, user_id: uuid.UUID, data: CategoryCreate) -> Category:
    name = data.name.strip()
    _ensure_unique_name(db, user_id, name)
    category = Category(user_id=user_id, name=name, type=data.type, is_default=False)
    db.add(category)
    db.commit()
    return category


def _get_owned(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
    category = get_category(db, user_id, category_id)
    if category.is_default or category.user_id != user_id:
        raise BadRequestError("Default categories cannot be modified")
    return category


def rename_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID, data: CategoryUpdate) -> Category:
    category = _get_owned(db, user_id, category_id)
    name = data.name.strip()
    _ensure_unique_name(db, user_id, name, exclude_id=category.id)
    category.name = name
    db.commit()
    return category


def deactivate_category(db: Session, user_id: uuid.UUID, category_id: uuid.UUID) -> None:
    category = _get_owned(db, user_id, category_id)
    category.is_active = False
    db.commit()
