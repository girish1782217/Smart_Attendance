from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.schemas.master_data.academic_class import (
    ClassCreateRequest,
    ClassResponse,
    ClassUpdateRequest,
)
from app.schemas.pagination import Page, PaginationParams
from app.services.master_data import class_service

router = APIRouter(prefix="/classes", tags=["master-data:classes"])


@router.post("", response_model=ClassResponse, status_code=201)
def create_class(
    payload: ClassCreateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> ClassResponse:
    academic_class = class_service.create_class(db, name=payload.name, program_id=payload.program_id)
    return ClassResponse.model_validate(academic_class)


@router.get("", response_model=Page[ClassResponse])
def list_classes(
    pagination: PaginationParams = Depends(),
    search: str | None = None,
    program_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> Page[ClassResponse]:
    items, total = class_service.list_classes(
        db, page=pagination.page, page_size=pagination.page_size, search=search, program_id=program_id
    )
    return Page(
        items=[ClassResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{class_id}", response_model=ClassResponse)
def get_class(
    class_id: int, db: Session = Depends(get_db), _current_user=Depends(get_current_user)
) -> ClassResponse:
    academic_class = class_service.get_class(db, class_id)
    return ClassResponse.model_validate(academic_class)


@router.patch("/{class_id}", response_model=ClassResponse)
def update_class(
    class_id: int,
    payload: ClassUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> ClassResponse:
    academic_class = class_service.update_class(
        db, class_id, name=payload.name, is_active=payload.is_active
    )
    return ClassResponse.model_validate(academic_class)


@router.delete("/{class_id}", response_model=ClassResponse)
def deactivate_class(
    class_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> ClassResponse:
    academic_class = class_service.deactivate_class(db, class_id)
    return ClassResponse.model_validate(academic_class)
