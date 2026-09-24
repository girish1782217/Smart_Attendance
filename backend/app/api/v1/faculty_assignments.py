from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.user import User
from app.schemas.faculty_assignment import FacultyAssignmentCreateRequest, FacultyAssignmentResponse
from app.schemas.pagination import Page, PaginationParams
from app.services import faculty_assignment_service, scoping

router = APIRouter(prefix="/faculty-assignments", tags=["faculty-assignments"])


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
    effective_faculty_id = scoping.resolve_faculty_filter(db, current_user, faculty_id)
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
