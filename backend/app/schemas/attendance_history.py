from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.models.attendance_record import AttendanceRecord
    from app.models.correction_request import CorrectionRequest


class AttendanceCounts(BaseModel):
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    percentage: float | None


class SubjectAttendanceSummary(AttendanceCounts):
    subject_id: int
    subject_name: str
    subject_code: str


class StudentAttendanceSummaryResponse(BaseModel):
    student_id: int
    overall: AttendanceCounts
    by_subject: list[SubjectAttendanceSummary]


class CorrectionSummary(BaseModel):
    original_status: str
    approved_status: str
    reason: str
    decision_reason: str | None
    reviewed_by_name: str | None
    reviewed_at: datetime | None

    @classmethod
    def from_model(cls, correction: "CorrectionRequest") -> "CorrectionSummary":
        return cls(
            original_status=correction.original_status.value,
            approved_status=correction.requested_status.value,
            reason=correction.reason,
            decision_reason=correction.decision_reason,
            reviewed_by_name=correction.reviewed_by.full_name if correction.reviewed_by else None,
            reviewed_at=correction.reviewed_at,
        )


class AttendanceHistoryRecordResponse(BaseModel):
    id: int
    session_id: int
    session_date: date
    start_time: time
    end_time: time
    subject_id: int
    subject_name: str
    subject_code: str
    status: str
    was_corrected: bool
    correction: CorrectionSummary | None

    @classmethod
    def from_model(
        cls, record: "AttendanceRecord", correction: "CorrectionRequest | None"
    ) -> "AttendanceHistoryRecordResponse":
        session = record.session
        subject = session.subject
        return cls(
            id=record.id,
            session_id=session.id,
            session_date=session.session_date,
            start_time=session.start_time,
            end_time=session.end_time,
            subject_id=subject.id,
            subject_name=subject.name,
            subject_code=subject.code,
            status=record.status.value,
            was_corrected=correction is not None,
            correction=CorrectionSummary.from_model(correction) if correction else None,
        )
