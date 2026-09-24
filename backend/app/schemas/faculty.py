from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class FacultyCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)
    employee_id: str = Field(min_length=1, max_length=30)
    department_id: int
    phone: str | None = Field(default=None, max_length=20)


class FacultyUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    department_id: int | None = None
    is_active: bool | None = None


class FacultyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: str
    full_name: str
    employee_id: str
    department_id: int
    phone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
