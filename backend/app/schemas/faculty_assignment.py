from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FacultyAssignmentCreateRequest(BaseModel):
    faculty_id: int
    subject_id: int
    section_id: int
    semester_id: int


class FacultyAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    faculty_id: int
    subject_id: int
    section_id: int
    semester_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
