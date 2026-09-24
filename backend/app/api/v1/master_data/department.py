from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.schemas.master_data.department import (
    DepartmentCreateRequest,
    DepartmentResponse,
    DepartmentUpdateRequest,
)
from app.schemas.pagination import Page, PaginationParams
from app.services.master_data import department_service

router = APIRouter(prefix="/departments", tags=["master-data:departments"])


@router.post("", response_model=DepartmentResponse, status_code=201)
def create_department(
    payload: DepartmentCreateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> DepartmentResponse:
    department = department_service.create_department(db, name=payload.name, code=payload.code)
    return DepartmentResponse.model_validate(department)


@router.get("", response_model=Page[DepartmentResponse])
def list_departments(
    pagination: PaginationParams = Depends(),
    search: str | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> Page[DepartmentResponse]:
    items, total = department_service.list_departments(
        db, page=pagination.page, page_size=pagination.page_size, search=search
    )
    return Page(
        items=[DepartmentResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: int, db: Session = Depends(get_db), _current_user=Depends(get_current_user)
) -> DepartmentResponse:
    department = department_service.get_department(db, department_id)
    return DepartmentResponse.model_validate(department)


@router.patch("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    payload: DepartmentUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> DepartmentResponse:
    department = department_service.update_department(
        db,
        department_id,
        name=payload.name,
        code=payload.code,
        is_active=payload.is_active,
    )
    return DepartmentResponse.model_validate(department)


@router.delete("/{department_id}", response_model=DepartmentResponse)
def deactivate_department(
    department_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> DepartmentResponse:
    department = department_service.deactivate_department(db, department_id)
    return DepartmentResponse.model_validate(department)
