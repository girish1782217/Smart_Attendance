from pydantic import BaseModel

from app.schemas.attendance_history import AttendanceCounts, SubjectAttendanceSummary


class AIInsightResponse(BaseModel):
    student_id: int
    overall: AttendanceCounts
    by_subject: list[SubjectAttendanceSummary]
    ai_available: bool
    insight_text: str | None
    ai_error_code: str | None
