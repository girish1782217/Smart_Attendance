from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.models.student import Student
from app.schemas.pagination import Page, PaginationParams
from app.schemas.student import StudentCreateRequest, StudentResponse, StudentUpdateRequest
from app.services import student_service

router = APIRouter(prefix="/students", tags=["students"])


def _to_response(student: Student) -> StudentResponse:
    return StudentResponse.from_model(student)


@router.post("", response_model=StudentResponse, status_code=201)
def create_student(
    payload: StudentCreateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> StudentResponse:
    student = student_service.create_student(
        db,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        roll_number=payload.roll_number,
        section_id=payload.section_id,
        phone=payload.phone,
    )
    return _to_response(student)


@router.get("", response_model=Page[StudentResponse])
def list_students(
    pagination: PaginationParams = Depends(),
    search: str | None = None,
    section_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> Page[StudentResponse]:
    items, total = student_service.list_students(
        db, page=pagination.page, page_size=pagination.page_size, search=search, section_id=section_id
    )
    return Page(
        items=[_to_response(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN, RoleName.FACULTY)),
) -> StudentResponse:
    student = student_service.get_student(db, student_id)
    return _to_response(student)


@router.patch("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    payload: StudentUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> StudentResponse:
    student = student_service.update_student(
        db,
        student_id,
        full_name=payload.full_name,
        phone=payload.phone,
        section_id=payload.section_id,
        is_active=payload.is_active,
    )
    return _to_response(student)


@router.delete("/{student_id}", response_model=StudentResponse)
def deactivate_student(
    student_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> StudentResponse:
    student = student_service.deactivate_student(db, student_id)
    return _to_response(student)
