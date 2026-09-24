from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.schemas.master_data.semester import (
    SemesterCreateRequest,
    SemesterResponse,
    SemesterUpdateRequest,
)
from app.schemas.pagination import Page, PaginationParams
from app.services.master_data import semester_service

router = APIRouter(prefix="/semesters", tags=["master-data:semesters"])


@router.post("", response_model=SemesterResponse, status_code=201)
def create_semester(
    payload: SemesterCreateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> SemesterResponse:
    semester = semester_service.create_semester(
        db,
        name=payload.name,
        academic_year_id=payload.academic_year_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    return SemesterResponse.model_validate(semester)


@router.get("", response_model=Page[SemesterResponse])
def list_semesters(
    pagination: PaginationParams = Depends(),
    search: str | None = None,
    academic_year_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> Page[SemesterResponse]:
    items, total = semester_service.list_semesters(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        search=search,
        academic_year_id=academic_year_id,
    )
    return Page(
        items=[SemesterResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{semester_id}", response_model=SemesterResponse)
def get_semester(
    semester_id: int, db: Session = Depends(get_db), _current_user=Depends(get_current_user)
) -> SemesterResponse:
    semester = semester_service.get_semester(db, semester_id)
    return SemesterResponse.model_validate(semester)


@router.patch("/{semester_id}", response_model=SemesterResponse)
def update_semester(
    semester_id: int,
    payload: SemesterUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> SemesterResponse:
    semester = semester_service.update_semester(
        db,
        semester_id,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_active=payload.is_active,
    )
    return SemesterResponse.model_validate(semester)


@router.delete("/{semester_id}", response_model=SemesterResponse)
def deactivate_semester(
    semester_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> SemesterResponse:
    semester = semester_service.deactivate_semester(db, semester_id)
    return SemesterResponse.model_validate(semester)
