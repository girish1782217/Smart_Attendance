import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.attendance_record import AttendanceStatus

if TYPE_CHECKING:
    from app.models.attendance_record import AttendanceRecord
    from app.models.user import User


class CorrectionRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CorrectionRequest(Base):
    """The controlled attendance-correction workflow (BR-3/BR-4). At most
    one PENDING request may exist per attendance record at a time — a
    partial unique index, not a blanket one, since a decided (approved or
    rejected) request must never block a later, new request on the same
    record."""

    __tablename__ = "correction_requests"
    __table_args__ = (
        Index(
            "uq_correction_pending_per_record",
            "attendance_record_id",
            unique=True,
            sqlite_where=text("status = 'PENDING'"),
            postgresql_where=text("status = 'PENDING'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    attendance_record_id: Mapped[int] = mapped_column(
        ForeignKey("attendance_records.id"), nullable=False, index=True
    )
    original_status: Mapped[AttendanceStatus] = mapped_column(
        SAEnum(AttendanceStatus, native_enum=False, length=20), nullable=False
    )
    requested_status: Mapped[AttendanceStatus] = mapped_column(
        SAEnum(AttendanceStatus, native_enum=False, length=20), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    status: Mapped[CorrectionRequestStatus] = mapped_column(
        SAEnum(CorrectionRequestStatus, native_enum=False, length=20),
        nullable=False,
        default=CorrectionRequestStatus.PENDING,
    )
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    attendance_record: Mapped["AttendanceRecord"] = relationship("AttendanceRecord")
    requested_by: Mapped["User"] = relationship("User", foreign_keys=[requested_by_user_id])
    reviewed_by: Mapped["User | None"] = relationship("User", foreign_keys=[reviewed_by_user_id])
