from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.schemas.master_data.subject import (
    SubjectCreateRequest,
    SubjectResponse,
    SubjectUpdateRequest,
)
from app.schemas.pagination import Page, PaginationParams
from app.services.master_data import subject_service

router = APIRouter(prefix="/subjects", tags=["master-data:subjects"])


@router.post("", response_model=SubjectResponse, status_code=201)
def create_subject(
    payload: SubjectCreateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> SubjectResponse:
    subject = subject_service.create_subject(
        db,
        name=payload.name,
        code=payload.code,
        department_id=payload.department_id,
        credits=payload.credits,
    )
    return SubjectResponse.model_validate(subject)


@router.get("", response_model=Page[SubjectResponse])
def list_subjects(
    pagination: PaginationParams = Depends(),
    search: str | None = None,
    department_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> Page[SubjectResponse]:
    items, total = subject_service.list_subjects(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        search=search,
        department_id=department_id,
    )
    return Page(
        items=[SubjectResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(
    subject_id: int, db: Session = Depends(get_db), _current_user=Depends(get_current_user)
) -> SubjectResponse:
    subject = subject_service.get_subject(db, subject_id)
    return SubjectResponse.model_validate(subject)


@router.patch("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    payload: SubjectUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> SubjectResponse:
    subject = subject_service.update_subject(
        db,
        subject_id,
        name=payload.name,
        code=payload.code,
        credits=payload.credits,
        is_active=payload.is_active,
    )
    return SubjectResponse.model_validate(subject)


@router.delete("/{subject_id}", response_model=SubjectResponse)
def deactivate_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> SubjectResponse:
    subject = subject_service.deactivate_subject(db, subject_id)
    return SubjectResponse.model_validate(subject)
