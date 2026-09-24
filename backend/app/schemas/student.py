from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)
    roll_number: str = Field(min_length=1, max_length=30)
    section_id: int
    phone: str | None = Field(default=None, max_length=20)


class StudentUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    section_id: int | None = None
    is_active: bool | None = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: str
    full_name: str
    roll_number: str
    section_id: int
    phone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
