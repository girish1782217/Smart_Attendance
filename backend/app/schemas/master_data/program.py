from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProgramCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=20)
    department_id: int


class ProgramUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=20)
    is_active: bool | None = None


class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    department_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
