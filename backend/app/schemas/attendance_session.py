from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING

from pydantic import BaseModel, model_validator

if TYPE_CHECKING:
    from app.models.attendance_session import AttendanceSession


class AttendanceSessionCreateRequest(BaseModel):
    # Required for ADMIN callers; ignored (overridden to the caller's own
    # linked Faculty id) for FACULTY callers — see app/services/scoping.py.
    faculty_id: int | None = None
    subject_id: int
    section_id: int
    session_date: date
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def _check_time_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AttendanceSessionResponse(BaseModel):
    id: int
    faculty_id: int
    faculty_name: str
    subject_id: int
    subject_name: str
    subject_code: str
    section_id: int
    section_name: str
    session_date: date
    start_time: time
    end_time: time
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, session: "AttendanceSession") -> "AttendanceSessionResponse":
        return cls(
            id=session.id,
            faculty_id=session.faculty_id,
            faculty_name=session.faculty.user.full_name,
            subject_id=session.subject_id,
            subject_name=session.subject.name,
            subject_code=session.subject.code,
            section_id=session.section_id,
            section_name=session.section.name,
            session_date=session.session_date,
            start_time=session.start_time,
            end_time=session.end_time,
            status=session.status.value,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
