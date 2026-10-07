import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

Money = Numeric(12, 2)
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


def enum_column(enum_class: type[enum.Enum], length: int = 20) -> Enum:
    return Enum(enum_class, native_enum=False, length=length)


def created_at_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()
