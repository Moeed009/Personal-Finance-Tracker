import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, created_at_column, enum_column, new_uuid


class AlertType(str, enum.Enum):
    BUDGET_WARNING = "BUDGET_WARNING"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    UNUSUAL_SPENDING = "UNUSUAL_SPENDING"
    RECURRING_DUE = "RECURRING_DUE"


class Alert(Base):
    __tablename__ = "alerts"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "reference_key",
            name="uq_alerts_user_reference",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=new_uuid,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    alert_type: Mapped[AlertType] = mapped_column(
        enum_column(AlertType),
    )

    message: Mapped[str] = mapped_column(
        String(400),
    )

    reference_key: Mapped[str | None] = mapped_column(
        String(120),
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = created_at_column()