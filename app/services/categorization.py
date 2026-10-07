import re
import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.transaction import TransactionType

EXPENSE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Food": ("foodpanda", "kfc", "restaurant", "grocery", "imtiaz", "pizza", "burger", "cafe", "bakery",
             "mcdonald", "carrefour", "naheed", "hotel"),
    "Transport": ("uber", "careem", "fuel", "petrol", "indrive", "bykea", "parking", "toll"),
    "Bills": ("k-electric", "lesco", "ptcl", "sui gas", "internet", "electricity", "wapda", "nayatel", "stormfiber"),
    "Shopping": ("daraz", "mall", "clothing", "khaadi", "outfitters", "amazon"),
    "Entertainment": ("netflix", "spotify", "cinema", "youtube premium", "steam", "xbox"),
    "Health": ("pharmacy", "hospital", "clinic", "doctor", "medical"),
    "Education": ("tuition", "school", "university", "udemy", "coursera"),
    "Housing": ("rent", "maintenance"),
    "Insurance": ("insurance", "takaful"),
    "Taxes": ("fbr",),
    "Charity": ("zakat", "sadqa", "donation", "charity"),
}

INCOME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Salary": ("salary",),
    "Freelance Income": ("freelance",),
    "Business Income": ("business income",),
    "Investment Income": ("dividend",),
    "Gifts Received": ("gift received", "eidi"),
    "Other Income": ("payment received",),
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _compile(table: dict[str, tuple[str, ...]]) -> list[tuple[str, re.Pattern]]:
    return [
        (name, re.compile("|".join(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])" for word in words)))
        for name, words in table.items()
    ]


_EXPENSE_PATTERNS = _compile(EXPENSE_KEYWORDS)
_INCOME_PATTERNS = _compile(INCOME_KEYWORDS)


def match_category_name(description: str, transaction_type: TransactionType) -> str | None:
    text = normalize(description)
    patterns = _INCOME_PATTERNS if transaction_type == TransactionType.INCOME else _EXPENSE_PATTERNS
    for name, pattern in patterns:
        if pattern.search(text):
            return name
    return None


def derive_merchant(description: str) -> str | None:
    cleaned = re.sub(r"[\d#*]+", " ", normalize(description))
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -_/.")
    return cleaned[:150] or None


class CategoryResolver:
    def __init__(self, db: Session, user_id: uuid.UUID):
        rows = db.scalars(
            select(Category).where(
                or_(Category.user_id == user_id, Category.is_default.is_(True)), Category.is_active.is_(True)
            )
        )
        self._by_name: dict[str, uuid.UUID] = {}
        for category in sorted(rows, key=lambda c: c.is_default, reverse=True):
            self._by_name[category.name.lower()] = category.id
        self.uncategorized_id = self._by_name.get("uncategorized")

    def resolve(self, description: str, transaction_type: TransactionType) -> uuid.UUID | None:
        name = match_category_name(description, transaction_type)
        if name and name.lower() in self._by_name:
            return self._by_name[name.lower()]
        return self.uncategorized_id
