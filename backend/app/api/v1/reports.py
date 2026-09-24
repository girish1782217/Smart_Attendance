from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.user import User
from app.schemas.low_attendance import (
    LowAttendanceBySubjectReportResponse,
    LowAttendanceOverallReportResponse,
)
from app.schemas.pagination import PaginationParams
from app.schemas.reports import (
    FacultyActivityReportResponse,
    SubjectAttendanceReportResponse,
    StudentAttendanceReportResponse,
)
from app.services import csv_export, low_attendance_service, report_service, scoping

router = APIRouter(prefix="/reports", tags=["reports"])

_OVERALL_CSV_FIELDS = [
    "student_id",
    "roll_number",
    "student_name",
    "present_count",
    "absent_count",
    "late_count",
    "excused_count",
    "total_applicable",
    "percentage",
]
_BY_SUBJECT_CSV_FIELDS = [
    "student_id",
    "roll_number",
    "student_name",
    "subject_id",
    "subject_name",
    "subject_code",
    "present_count",
    "absent_count",
    "late_count",
    "excused_count",
    "total_applicable",
    "percentage",
]


def _csv_response(rows: list[dict], fieldnames: list[str], filename: str) -> Response:
    csv_text = csv_export.rows_to_csv(rows, fieldnames)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/low-attendance/overall", response_model=LowAttendanceOverallReportResponse)
def low_attendance_overall(
    pagination: PaginationParams = Depends(),
    department_id: int | None = None,
    class_id: int | None = None,
    section_id: int | None = None,
    search: str | None = None,
    threshold: float | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> LowAttendanceOverallReportResponse:
    items, total, effective_threshold = low_attendance_service.get_overall_low_attendance(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        search=search,
        threshold=threshold,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return LowAttendanceOverallReportResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        threshold=effective_threshold,
    )


@router.get("/low-attendance/by-subject", response_model=LowAttendanceBySubjectReportResponse)
def low_attendance_by_subject(
    pagination: PaginationParams = Depends(),
    department_id: int | None = None,
    class_id: int | None = None,
    section_id: int | None = None,
    subject_id: int | None = None,
    search: str | None = None,
    threshold: float | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> LowAttendanceBySubjectReportResponse:
    items, total, effective_threshold = low_attendance_service.get_by_subject_low_attendance(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        search=search,
        threshold=threshold,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return LowAttendanceBySubjectReportResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        threshold=effective_threshold,
    )


@router.get("/low-attendance/overall/export")
def export_low_attendance_overall(
    department_id: int | None = None,
    class_id: int | None = None,
    section_id: int | None = None,
    search: str | None = None,
    threshold: float | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> Response:
    items, _effective_threshold = low_attendance_service.get_overall_full(
        db, department_id=department_id, class_id=class_id, section_id=section_id, search=search, threshold=threshold
    )
    return _csv_response(items, _OVERALL_CSV_FIELDS, "low_attendance_overall.csv")


@router.get("/low-attendance/by-subject/export")
def export_low_attendance_by_subject(
    department_id: int | None = None,
    class_id: int | None = None,
    section_id: int | None = None,
    subject_id: int | None = None,
    search: str | None = None,
    threshold: float | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> Response:
    items, _effective_threshold = low_attendance_service.get_by_subject_full(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        search=search,
        threshold=threshold,
    )
    return _csv_response(items, _BY_SUBJECT_CSV_FIELDS, "low_attendance_by_subject.csv")


@router.get("/student-attendance", response_model=StudentAttendanceReportResponse)
def student_attendance_report(
    pagination: PaginationParams = Depends(),
    department_id: int | None = None,
    class_id: int | None = None,
    section_id: int | None = None,
    student_id: int | None = None,
    search: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> StudentAttendanceReportResponse:
    items, total = report_service.get_student_attendance_report(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        student_id=student_id,
        search=search,
        from_date=from_date,
        to_date=to_date,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return StudentAttendanceReportResponse(
        items=items, total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/student-attendance/export")
def export_student_attendance_report(
    department_id: int | None = None,
    class_id: int | None = None,
    section_id: int | None = None,
    student_id: int | None = None,
    search: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> Response:
    items, _total = report_service.get_student_attendance_report(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        student_id=student_id,
        search=search,
        from_date=from_date,
        to_date=to_date,
    )
    return _csv_response(items, _OVERALL_CSV_FIELDS, "student_attendance_report.csv")


@router.get("/subject-attendance", response_model=SubjectAttendanceReportResponse)
def subject_attendance_report(
    pagination: PaginationParams = Depends(),
    department_id: int | None = None,
    class_id: int | None = None,
    section_id: int | None = None,
    subject_id: int | None = None,
    student_id: int | None = None,
    search: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> SubjectAttendanceReportResponse:
    items, total = report_service.get_subject_attendance_report(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        student_id=student_id,
        search=search,
        from_date=from_date,
        to_date=to_date,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return SubjectAttendanceReportResponse(
        items=items, total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/subject-attendance/export")
def export_subject_attendance_report(
    department_id: int | None = None,
    class_id: int | None = None,
    section_id: int | None = None,
    subject_id: int | None = None,
    student_id: int | None = None,
    search: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> Response:
    items, _total = report_service.get_subject_attendance_report(
        db,
        department_id=department_id,
        class_id=class_id,
        section_id=section_id,
        subject_id=subject_id,
        student_id=student_id,
        search=search,
        from_date=from_date,
        to_date=to_date,
    )
    return _csv_response(items, _BY_SUBJECT_CSV_FIELDS, "subject_attendance_report.csv")


@router.get("/faculty-activity", response_model=FacultyActivityReportResponse)
def faculty_activity_report(
    faculty_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> FacultyActivityReportResponse:
    # Same "ADMIN must specify explicitly, FACULTY always their own" rule
    # as write endpoints elsewhere (app/services/scoping.py) — reused here
    # because a report always needs exactly one target faculty, same as a
    # create action does.
    effective_faculty_id = scoping.resolve_faculty_for_write(db, current_user, faculty_id)
    report = report_service.get_faculty_activity_report(
        db, faculty_id=effective_faculty_id, from_date=from_date, to_date=to_date
    )
    return FacultyActivityReportResponse.model_validate(report)
