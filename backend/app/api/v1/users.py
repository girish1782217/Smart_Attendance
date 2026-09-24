from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.roles import RoleName
from app.schemas.pagination import Page, PaginationParams
from app.schemas.user import AssignRolesRequest, CreateUserRequest, UserWithRolesResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserWithRolesResponse, status_code=201)
def create_user(
    payload: CreateUserRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> UserWithRolesResponse:
    user = user_service.create_user_with_roles(
        db,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role_names=payload.role_names,
    )
    return UserWithRolesResponse.from_model(user)


@router.get("", response_model=Page[UserWithRolesResponse])
def list_users(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> Page[UserWithRolesResponse]:
    users, total = user_service.list_users(db, page=pagination.page, page_size=pagination.page_size)
    return Page(
        items=[UserWithRolesResponse.from_model(user) for user in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.put("/{user_id}/roles", response_model=UserWithRolesResponse)
def set_user_roles(
    user_id: int,
    payload: AssignRolesRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_role(RoleName.ADMIN)),
) -> UserWithRolesResponse:
    user = user_service.set_user_roles(db, user_id=user_id, role_names=payload.role_names)
    return UserWithRolesResponse.from_model(user)
