import enum
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.faculty import Faculty
    from app.models.section import Section
    from app.models.subject import Subject


class AttendanceSessionStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    SUBMITTED = "SUBMITTED"


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    __table_args__ = (
        Index("ix_attendance_sessions_section_date", "section_id", "session_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id"), nullable=False, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False, index=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False, index=True)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    # native_enum=False -> portable VARCHAR+CHECK across SQLite/Postgres;
    # adding a status value later needs no `ALTER TYPE` migration.
    status: Mapped[AttendanceSessionStatus] = mapped_column(
        SAEnum(AttendanceSessionStatus, native_enum=False, length=20),
        nullable=False,
        default=AttendanceSessionStatus.SCHEDULED,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    faculty: Mapped["Faculty"] = relationship("Faculty")
    subject: Mapped["Subject"] = relationship("Subject")
    section: Mapped["Section"] = relationship("Section")
