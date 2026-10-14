from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_type: str
    title: str
    body: str | None
    reference_type: str | None
    reference_id: UUID | None
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    limit: int
    offset: int


class UnreadCountResponse(BaseModel):
    unread_count: int = Field(ge=0)


class MarkAllReadResponse(BaseModel):
    updated_count: int = Field(ge=0)