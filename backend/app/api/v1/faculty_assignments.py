from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.roles import RoleName
from app.models.user import User
from app.repositories import faculty_repository
from app.schemas.faculty_assignment import FacultyAssignmentCreateRequest, FacultyAssignmentResponse
from app.schemas.pagination import Page, PaginationParams
from app.services import faculty_assignment_service

router = APIRouter(prefix="/faculty-assignments", tags=["faculty-assignments"])


def _resolve_effective_faculty_filter(
    db: Session, current_user: User, requested_faculty_id: int | None
) -> int | None:
    """ADMIN may filter by any faculty_id (or none, to see everyone's
    assignments). A FACULTY-role caller is always scoped to their own
    assignments — any faculty_id they pass is ignored, not merely validated,
    so there is no way to read another faculty member's assignments by
    guessing an id (see AC7 in 06-faculty-management-spec.md)."""
    role_names = {role.name for role in current_user.roles}
    if RoleName.ADMIN.value in role_names:
        return requested_faculty_id

    own_faculty = faculty_repository.get_by_user_id(db, current_user.id)
    if own_faculty is None:
        raise NotFoundError(
            "No faculty profile is linked to the current user.", code="FACULTY_PROFILE_NOT_FOUND"
        )
    return own_faculty.id


@router.post("", response_model=FacultyAssignmentResponse, status_code=201)
def create_assignment(
    payload: FacultyAssignmentCreateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> FacultyAssignmentResponse:
    assignment = faculty_assignment_service.create_assignment(
        db,
        faculty_id=payload.faculty_id,
        subject_id=payload.subject_id,
        section_id=payload.section_id,
        semester_id=payload.semester_id,
    )
    return FacultyAssignmentResponse.model_validate(assignment)


@router.get("", response_model=Page[FacultyAssignmentResponse])
def list_assignments(
    pagination: PaginationParams = Depends(),
    faculty_id: int | None = None,
    subject_id: int | None = None,
    section_id: int | None = None,
    semester_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> Page[FacultyAssignmentResponse]:
    effective_faculty_id = _resolve_effective_faculty_filter(db, current_user, faculty_id)
    items, total = faculty_assignment_service.list_assignments(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        faculty_id=effective_faculty_id,
        subject_id=subject_id,
        section_id=section_id,
        semester_id=semester_id,
    )
    return Page(
        items=[FacultyAssignmentResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{assignment_id}", response_model=FacultyAssignmentResponse)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> FacultyAssignmentResponse:
    assignment = faculty_assignment_service.get_assignment(db, assignment_id)
    return FacultyAssignmentResponse.model_validate(assignment)


@router.delete("/{assignment_id}", response_model=FacultyAssignmentResponse)
def deactivate_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> FacultyAssignmentResponse:
    assignment = faculty_assignment_service.deactivate_assignment(db, assignment_id)
    return FacultyAssignmentResponse.model_validate(assignment)
