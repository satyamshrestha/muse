from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MoodEntryCreate(BaseModel):
    mood: str = Field(min_length=1, max_length=50)
    intensity: int = Field(ge=1, le=5)
    note: str | None = Field(default=None, max_length=500)


class MoodEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    mood: str
    intensity: int
    note: str | None
    created_at: datetime