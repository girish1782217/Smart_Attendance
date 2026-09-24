from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SemesterCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    academic_year_id: int
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def _check_date_order(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class SemesterUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _check_date_order(self):
        if self.start_date is not None and self.end_date is not None:
            if self.end_date <= self.start_date:
                raise ValueError("end_date must be after start_date")
        return self


class SemesterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    academic_year_id: int
    start_date: date
    end_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime
