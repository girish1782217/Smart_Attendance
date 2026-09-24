from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SectionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    class_id: int
    capacity: int | None = Field(default=None, ge=1)


class SectionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    capacity: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class SectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    class_id: int
    capacity: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
