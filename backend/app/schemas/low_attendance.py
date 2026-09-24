from pydantic import BaseModel


class LowAttendanceOverallRow(BaseModel):
    student_id: int
    roll_number: str
    student_name: str
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    total_applicable: int
    percentage: float


class LowAttendanceBySubjectRow(LowAttendanceOverallRow):
    subject_id: int
    subject_name: str
    subject_code: str


class LowAttendanceOverallReportResponse(BaseModel):
    items: list[LowAttendanceOverallRow]
    total: int
    page: int
    page_size: int
    threshold: float


class LowAttendanceBySubjectReportResponse(BaseModel):
    items: list[LowAttendanceBySubjectRow]
    total: int
    page: int
    page_size: int
    threshold: float
