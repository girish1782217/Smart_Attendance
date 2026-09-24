from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.correction_request import CorrectionRequestStatus
from app.models.user import User
from app.schemas.correction import CorrectionDecisionRequest, CorrectionResponse
from app.schemas.pagination import Page, PaginationParams
from app.services import correction_service, scoping

router = APIRouter(prefix="/corrections", tags=["corrections"])


def _role_names(user: User) -> set[str]:
    return {role.name for role in user.roles}


@router.get("", response_model=Page[CorrectionResponse])
def list_corrections(
    pagination: PaginationParams = Depends(),
    status: CorrectionRequestStatus | None = None,
    attendance_record_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY, RoleName.STUDENT)),
) -> Page[CorrectionResponse]:
    roles = _role_names(current_user)
    faculty_id = None
    student_id = None
    if RoleName.ADMIN.value not in roles:
        if RoleName.FACULTY.value in roles:
            faculty_id = scoping.resolve_faculty_filter(db, current_user, None)
        elif RoleName.STUDENT.value in roles:
            student_id = scoping.resolve_own_student_id(db, current_user)

    items, total = correction_service.list_corrections(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        status=status,
        attendance_record_id=attendance_record_id,
        faculty_id=faculty_id,
        student_id=student_id,
    )
    return Page(
        items=[CorrectionResponse.from_model(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{correction_id}", response_model=CorrectionResponse)
def get_correction(
    correction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY, RoleName.STUDENT)),
) -> CorrectionResponse:
    correction = correction_service.get_correction(db, correction_id)
    correction_service.ensure_can_view(db, current_user, correction)
    return CorrectionResponse.from_model(correction)


@router.post("/{correction_id}/approve", response_model=CorrectionResponse)
def approve_correction(
    correction_id: int,
    payload: CorrectionDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> CorrectionResponse:
    correction = correction_service.approve_correction(
        db, correction_id=correction_id, current_user=current_user, decision_reason=payload.decision_reason
    )
    return CorrectionResponse.from_model(correction)


@router.post("/{correction_id}/reject", response_model=CorrectionResponse)
def reject_correction(
    correction_id: int,
    payload: CorrectionDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> CorrectionResponse:
    correction = correction_service.reject_correction(
        db, correction_id=correction_id, current_user=current_user, decision_reason=payload.decision_reason
    )
    return CorrectionResponse.from_model(correction)
