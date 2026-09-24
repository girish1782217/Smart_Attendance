from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.schemas.low_attendance import (
    LowAttendanceBySubjectReportResponse,
    LowAttendanceOverallReportResponse,
)
from app.schemas.pagination import PaginationParams
from app.services import low_attendance_service

router = APIRouter(prefix="/reports", tags=["reports"])


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
