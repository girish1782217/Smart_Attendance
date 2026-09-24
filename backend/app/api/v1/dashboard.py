from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.user import User
from app.schemas.attendance_history import AttendanceHistoryRecordResponse
from app.schemas.dashboard import AdminDashboardResponse, FacultyDashboardResponse, StudentDashboardResponse
from app.services import dashboard_service, scoping

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/admin", response_model=AdminDashboardResponse)
def admin_dashboard(
    db: Session = Depends(get_db), _current_user=Depends(require_role(RoleName.ADMIN))
) -> AdminDashboardResponse:
    data = dashboard_service.get_admin_dashboard(db)
    return AdminDashboardResponse.model_validate(data)


@router.get("/faculty", response_model=FacultyDashboardResponse)
def faculty_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.FACULTY)),
) -> FacultyDashboardResponse:
    # FACULTY only (not ADMIN) -- always the caller's own; an ADMIN wanting
    # a specific faculty member's numbers uses SPEC 12's faculty-activity
    # report instead (see design note in docs/sdd/14-dashboard-spec.md AC1).
    # resolve_faculty_filter with requested=None resolves to "own" for any
    # non-admin caller, which every caller here is (require_role above).
    faculty_id = scoping.resolve_faculty_filter(db, current_user, None)
    data = dashboard_service.get_faculty_dashboard(db, faculty_id=faculty_id)
    return FacultyDashboardResponse.model_validate(data)


@router.get("/student", response_model=StudentDashboardResponse)
def student_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.STUDENT)),
) -> StudentDashboardResponse:
    student_id = scoping.resolve_own_student_id(db, current_user)
    data = dashboard_service.get_student_dashboard(db, student_id=student_id)
    recent_attendance = [
        AttendanceHistoryRecordResponse.from_model(
            record, data["recent_corrections_by_record_id"].get(record.id)
        )
        for record in data["recent_records"]
    ]
    return StudentDashboardResponse(
        overall=data["overall"],
        by_subject=data["by_subject"],
        recent_attendance=recent_attendance,
        is_low_attendance=data["is_low_attendance"],
        threshold=data["threshold"],
        pending_correction_requests=data["pending_correction_requests"],
    )
