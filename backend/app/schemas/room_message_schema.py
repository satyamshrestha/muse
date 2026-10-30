from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoomMessageCreate(BaseModel):
    content: str = Field(min_length=1)


class RoomMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group_id: UUID
    user_id: UUID
    content: str
    created_at: datetime