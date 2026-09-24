from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.models.attendance_record import AttendanceStatus

if TYPE_CHECKING:
    from app.models.correction_request import CorrectionRequest


class CorrectionCreateRequest(BaseModel):
    requested_status: AttendanceStatus
    reason: str = Field(min_length=1, max_length=1000)


class CorrectionDecisionRequest(BaseModel):
    decision_reason: str | None = Field(default=None, max_length=1000)


class CorrectionResponse(BaseModel):
    id: int
    attendance_record_id: int
    student_id: int
    student_name: str
    session_id: int
    original_status: str
    requested_status: str
    reason: str
    requested_by_user_id: int
    requested_by_name: str
    requested_at: datetime
    status: str
    reviewed_by_user_id: int | None
    reviewed_by_name: str | None
    reviewed_at: datetime | None
    decision_reason: str | None

    @classmethod
    def from_model(cls, correction: "CorrectionRequest") -> "CorrectionResponse":
        record = correction.attendance_record
        return cls(
            id=correction.id,
            attendance_record_id=correction.attendance_record_id,
            student_id=record.student_id,
            student_name=record.student.user.full_name,
            session_id=record.session_id,
            original_status=correction.original_status.value,
            requested_status=correction.requested_status.value,
            reason=correction.reason,
            requested_by_user_id=correction.requested_by_user_id,
            requested_by_name=correction.requested_by.full_name,
            requested_at=correction.requested_at,
            status=correction.status.value,
            reviewed_by_user_id=correction.reviewed_by_user_id,
            reviewed_by_name=correction.reviewed_by.full_name if correction.reviewed_by else None,
            reviewed_at=correction.reviewed_at,
            decision_reason=correction.decision_reason,
        )
