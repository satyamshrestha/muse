from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GroupActivityResponseCreate(BaseModel):
    response: str = Field(min_length=1, max_length=100)
    note: str | None = None


class GroupActivityResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activity_id: UUID
    user_id: UUID
    response: str
    note: str | None
    created_at: datetime