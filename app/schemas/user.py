import uuid
from pydantic import BaseModel, Field

from pydantic import BaseModel, Field, field_validator

from app.models.user import User


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    currency: str

    @classmethod
    def from_user(cls, user: User) -> "UserRead":
        return cls(id=user.id, email=user.email, full_name=user.full_name, currency=user.profile.currency)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    currency: str | None = None
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=72)

    @field_validator("currency")
    @classmethod
    def upper_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value
