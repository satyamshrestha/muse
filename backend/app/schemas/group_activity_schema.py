from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GroupActivityCreate(BaseModel):
    activity_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class GroupActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group_id: UUID
    created_by: UUID
    activity_type: str
    title: str
    description: str | None
    created_at: datetime