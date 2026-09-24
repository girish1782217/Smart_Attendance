from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.user import User
from app.schemas.attendance_history import (
    AttendanceHistoryRecordResponse,
    StudentAttendanceSummaryResponse,
)
from app.schemas.pagination import Page, PaginationParams
from app.services import attendance_history_service, scoping

router = APIRouter(prefix="/students", tags=["attendance-history"])


@router.get("/{student_id}/attendance-summary", response_model=StudentAttendanceSummaryResponse)
def get_attendance_summary(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY, RoleName.STUDENT)),
) -> StudentAttendanceSummaryResponse:
    faculty_scope = scoping.resolve_student_access_scope(db, current_user, student_id)
    summary = attendance_history_service.get_summary(db, student_id=student_id, faculty_id=faculty_scope)
    return StudentAttendanceSummaryResponse.model_validate(summary)


@router.get("/{student_id}/attendance-history", response_model=Page[AttendanceHistoryRecordResponse])
def get_attendance_history(
    student_id: int,
    pagination: PaginationParams = Depends(),
    subject_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY, RoleName.STUDENT)),
) -> Page[AttendanceHistoryRecordResponse]:
    faculty_scope = scoping.resolve_student_access_scope(db, current_user, student_id)
    records, corrections_by_record_id, total = attendance_history_service.get_history(
        db,
        student_id=student_id,
        subject_id=subject_id,
        faculty_id=faculty_scope,
        from_date=from_date,
        to_date=to_date,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    items = [
        AttendanceHistoryRecordResponse.from_model(record, corrections_by_record_id.get(record.id))
        for record in records
    ]
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
