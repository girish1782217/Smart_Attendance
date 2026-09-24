from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=20)
    department_id: int
    credits: int | None = Field(default=None, ge=1, le=20)


class SubjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=20)
    credits: int | None = Field(default=None, ge=1, le=20)
    is_active: bool | None = None


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    department_id: int
    credits: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
