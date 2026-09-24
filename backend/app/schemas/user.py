from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.roles import RoleName

if TYPE_CHECKING:
    from app.models.user import User


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


class UserWithRolesResponse(UserResponse):
    roles: list[str]

    @classmethod
    def from_model(cls, user: "User") -> "UserWithRolesResponse":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            roles=[role.name for role in user.roles],
        )


class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)
    role_names: list[RoleName] = Field(min_length=1)


class AssignRolesRequest(BaseModel):
    role_names: list[RoleName] = Field(min_length=1)
