import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditAction(str, enum.Enum):
    CORRECTION_REQUESTED = "ATTENDANCE_CORRECTION_REQUESTED"
    CORRECTION_APPROVED = "ATTENDANCE_CORRECTION_APPROVED"
    CORRECTION_REJECTED = "ATTENDANCE_CORRECTION_REJECTED"


class AuditLog(Base):
    """Generic audit trail. Introduced in SPEC 09 for the correction
    workflow specifically — see the Scope Note in
    docs/sdd/09-attendance-correction-spec.md for why earlier specs'
    mutations aren't retroactively logged here."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(nullable=False, index=True)
    before_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    after_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    actor: Mapped["User"] = relationship("User")
