from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.faculty import Faculty
from app.schemas.faculty import FacultyCreateRequest, FacultyResponse, FacultyUpdateRequest
from app.schemas.pagination import Page, PaginationParams
from app.services import faculty_service

router = APIRouter(prefix="/faculty", tags=["faculty"])


def _to_response(faculty: Faculty) -> FacultyResponse:
    return FacultyResponse(
        id=faculty.id,
        user_id=faculty.user_id,
        email=faculty.user.email,
        full_name=faculty.user.full_name,
        employee_id=faculty.employee_id,
        department_id=faculty.department_id,
        phone=faculty.phone,
        is_active=faculty.is_active,
        created_at=faculty.created_at,
        updated_at=faculty.updated_at,
    )


@router.post("", response_model=FacultyResponse, status_code=201)
def create_faculty(
    payload: FacultyCreateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> FacultyResponse:
    faculty = faculty_service.create_faculty(
        db,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        employee_id=payload.employee_id,
        department_id=payload.department_id,
        phone=payload.phone,
    )
    return _to_response(faculty)


@router.get("", response_model=Page[FacultyResponse])
def list_faculty(
    pagination: PaginationParams = Depends(),
    search: str | None = None,
    department_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> Page[FacultyResponse]:
    items, total = faculty_service.list_faculty(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        search=search,
        department_id=department_id,
    )
    return Page(
        items=[_to_response(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{faculty_id}", response_model=FacultyResponse)
def get_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> FacultyResponse:
    faculty = faculty_service.get_faculty(db, faculty_id)
    return _to_response(faculty)


@router.patch("/{faculty_id}", response_model=FacultyResponse)
def update_faculty(
    faculty_id: int,
    payload: FacultyUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> FacultyResponse:
    faculty = faculty_service.update_faculty(
        db,
        faculty_id,
        full_name=payload.full_name,
        phone=payload.phone,
        department_id=payload.department_id,
        is_active=payload.is_active,
    )
    return _to_response(faculty)


@router.delete("/{faculty_id}", response_model=FacultyResponse)
def deactivate_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> FacultyResponse:
    faculty = faculty_service.deactivate_faculty(db, faculty_id)
    return _to_response(faculty)
