from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.schemas.master_data.academic_year import (
    AcademicYearCreateRequest,
    AcademicYearResponse,
    AcademicYearUpdateRequest,
)
from app.schemas.pagination import Page, PaginationParams
from app.services.master_data import academic_year_service

router = APIRouter(prefix="/academic-years", tags=["master-data:academic-years"])


@router.post("", response_model=AcademicYearResponse, status_code=201)
def create_academic_year(
    payload: AcademicYearCreateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> AcademicYearResponse:
    year = academic_year_service.create_academic_year(
        db, name=payload.name, start_date=payload.start_date, end_date=payload.end_date
    )
    return AcademicYearResponse.model_validate(year)


@router.get("", response_model=Page[AcademicYearResponse])
def list_academic_years(
    pagination: PaginationParams = Depends(),
    search: str | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> Page[AcademicYearResponse]:
    items, total = academic_year_service.list_academic_years(
        db, page=pagination.page, page_size=pagination.page_size, search=search
    )
    return Page(
        items=[AcademicYearResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{academic_year_id}", response_model=AcademicYearResponse)
def get_academic_year(
    academic_year_id: int, db: Session = Depends(get_db), _current_user=Depends(get_current_user)
) -> AcademicYearResponse:
    year = academic_year_service.get_academic_year(db, academic_year_id)
    return AcademicYearResponse.model_validate(year)


@router.patch("/{academic_year_id}", response_model=AcademicYearResponse)
def update_academic_year(
    academic_year_id: int,
    payload: AcademicYearUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> AcademicYearResponse:
    year = academic_year_service.update_academic_year(
        db,
        academic_year_id,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_active=payload.is_active,
    )
    return AcademicYearResponse.model_validate(year)


@router.delete("/{academic_year_id}", response_model=AcademicYearResponse)
def deactivate_academic_year(
    academic_year_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> AcademicYearResponse:
    year = academic_year_service.deactivate_academic_year(db, academic_year_id)
    return AcademicYearResponse.model_validate(year)
