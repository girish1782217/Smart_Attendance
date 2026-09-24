from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.schemas.master_data.program import (
    ProgramCreateRequest,
    ProgramResponse,
    ProgramUpdateRequest,
)
from app.schemas.pagination import Page, PaginationParams
from app.services.master_data import program_service

router = APIRouter(prefix="/programs", tags=["master-data:programs"])


@router.post("", response_model=ProgramResponse, status_code=201)
def create_program(
    payload: ProgramCreateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> ProgramResponse:
    program = program_service.create_program(
        db, name=payload.name, code=payload.code, department_id=payload.department_id
    )
    return ProgramResponse.model_validate(program)


@router.get("", response_model=Page[ProgramResponse])
def list_programs(
    pagination: PaginationParams = Depends(),
    search: str | None = None,
    department_id: int | None = None,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> Page[ProgramResponse]:
    items, total = program_service.list_programs(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        search=search,
        department_id=department_id,
    )
    return Page(
        items=[ProgramResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{program_id}", response_model=ProgramResponse)
def get_program(
    program_id: int, db: Session = Depends(get_db), _current_user=Depends(get_current_user)
) -> ProgramResponse:
    program = program_service.get_program(db, program_id)
    return ProgramResponse.model_validate(program)


@router.patch("/{program_id}", response_model=ProgramResponse)
def update_program(
    program_id: int,
    payload: ProgramUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> ProgramResponse:
    program = program_service.update_program(
        db, program_id, name=payload.name, code=payload.code, is_active=payload.is_active
    )
    return ProgramResponse.model_validate(program)


@router.delete("/{program_id}", response_model=ProgramResponse)
def deactivate_program(
    program_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> ProgramResponse:
    program = program_service.deactivate_program(db, program_id)
    return ProgramResponse.model_validate(program)
