from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str
    message: str
    related_entity_type: str | None
    related_entity_id: int | None
    is_read: bool
    created_at: datetime
    read_at: datetime | None
