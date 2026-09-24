from pydantic import BaseModel

from app.schemas.attendance_history import (
    AttendanceCounts,
    AttendanceHistoryRecordResponse,
    SubjectAttendanceSummary,
)


class AdminDashboardResponse(BaseModel):
    total_students: int
    total_faculty: int
    total_departments: int
    total_classes: int
    today_sessions_total: int
    today_sessions_submitted: int
    overall_attendance_percentage: float | None
    students_below_threshold: int
    pending_correction_requests: int


class FacultyDashboardResponse(BaseModel):
    assigned_sections: int
    today_sessions: int
    total_sessions: int
    students_below_threshold: int
    pending_correction_requests: int


class StudentDashboardResponse(BaseModel):
    overall: AttendanceCounts
    by_subject: list[SubjectAttendanceSummary]
    recent_attendance: list[AttendanceHistoryRecordResponse]
    is_low_attendance: bool
    threshold: float
    pending_correction_requests: int
