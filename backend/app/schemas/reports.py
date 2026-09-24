from datetime import date

from pydantic import BaseModel

from app.schemas.low_attendance import LowAttendanceBySubjectRow, LowAttendanceOverallRow

# Same row shape as the SPEC 11 low-attendance reports (student/subject +
# counts + percentage) — these reports just skip the threshold cutoff.
StudentAttendanceRow = LowAttendanceOverallRow
SubjectAttendanceRow = LowAttendanceBySubjectRow


class StudentAttendanceReportResponse(BaseModel):
    items: list[StudentAttendanceRow]
    total: int
    page: int
    page_size: int


class SubjectAttendanceReportResponse(BaseModel):
    items: list[SubjectAttendanceRow]
    total: int
    page: int
    page_size: int


class FacultyActivityReportResponse(BaseModel):
    faculty_id: int
    total_sessions: int
    submitted_sessions: int
    scheduled_sessions: int
    from_date: date | None
    to_date: date | None
