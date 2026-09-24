from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.roles import RoleName


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


class UserWithRolesResponse(UserResponse):
    roles: list[str]


class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)
    role_names: list[RoleName] = Field(min_length=1)


class AssignRolesRequest(BaseModel):
    role_names: list[RoleName] = Field(min_length=1)
