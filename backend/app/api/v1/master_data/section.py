from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.schemas.master_data.section import (
    SectionCreateRequest,
    SectionResponse,
    SectionUpdateRequest,
)
from app.schemas.pagination import Page, PaginationParams
from app.services.master_data import section_service

router = APIRouter(prefix="/sections", tags=["master-data:sections"])


@router.post("", response_model=SectionResponse, status_code=201)
def create_section(
    payload: SectionCreateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> SectionResponse:
    section = section_service.create_section(
        db, name=payload.name, class_id=payload.class_id, capacity=payload.capacity
    )
    return SectionResponse.model_validate(section)


@router.get("", response_model=Page[SectionResponse])
def list_sections(
    pagination: PaginationParams = Depends(),
    search: str | None = None,
    class_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> Page[SectionResponse]:
    items, total = section_service.list_sections(
        db, page=pagination.page, page_size=pagination.page_size, search=search, class_id=class_id
    )
    return Page(
        items=[SectionResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{section_id}", response_model=SectionResponse)
def get_section(
    section_id: int, db: Session = Depends(get_db), _current_user=Depends(get_current_user)
) -> SectionResponse:
    section = section_service.get_section(db, section_id)
    return SectionResponse.model_validate(section)


@router.patch("/{section_id}", response_model=SectionResponse)
def update_section(
    section_id: int,
    payload: SectionUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> SectionResponse:
    section = section_service.update_section(
        db, section_id, name=payload.name, capacity=payload.capacity, is_active=payload.is_active
    )
    return SectionResponse.model_validate(section)


@router.delete("/{section_id}", response_model=SectionResponse)
def deactivate_section(
    section_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> SectionResponse:
    section = section_service.deactivate_section(db, section_id)
    return SectionResponse.model_validate(section)
