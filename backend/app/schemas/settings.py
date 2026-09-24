from pydantic import BaseModel, Field


class LowAttendanceThresholdResponse(BaseModel):
    threshold: float


class LowAttendanceThresholdUpdateRequest(BaseModel):
    threshold: float = Field(gt=0, le=100)
