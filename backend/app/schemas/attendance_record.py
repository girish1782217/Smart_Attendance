from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

from app.models.attendance_record import AttendanceStatus

if TYPE_CHECKING:
    from app.models.attendance_record import AttendanceRecord


class AttendanceMarkItem(BaseModel):
    student_id: int
    status: AttendanceStatus


class BulkMarkRequest(BaseModel):
    records: list[AttendanceMarkItem] = Field(min_length=1)

    @model_validator(mode="after")
    def _no_duplicate_students_in_one_request(self):
        student_ids = [item.student_id for item in self.records]
        if len(student_ids) != len(set(student_ids)):
            raise ValueError("Each student_id may appear at most once per bulk-mark request.")
        return self


class AttendanceRecordResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    roll_number: str
    student_name: str
    status: str
    recorded_by_user_id: int
    recorded_at: datetime

    @classmethod
    def from_model(cls, record: "AttendanceRecord") -> "AttendanceRecordResponse":
        return cls(
            id=record.id,
            session_id=record.session_id,
            student_id=record.student_id,
            roll_number=record.student.roll_number,
            student_name=record.student.user.full_name,
            status=record.status.value,
            recorded_by_user_id=record.recorded_by_user_id,
            recorded_at=record.recorded_at,
        )
