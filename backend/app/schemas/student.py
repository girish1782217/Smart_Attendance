from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, EmailStr, Field

if TYPE_CHECKING:
    from app.models.student import Student


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

    @classmethod
    def from_model(cls, student: "Student") -> "StudentResponse":
        return cls(
            id=student.id,
            user_id=student.user_id,
            email=student.user.email,
            full_name=student.user.full_name,
            roll_number=student.roll_number,
            section_id=student.section_id,
            phone=student.phone,
            is_active=student.is_active,
            created_at=student.created_at,
            updated_at=student.updated_at,
        )
