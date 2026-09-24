from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClassCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    program_id: int


class ClassUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    program_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
