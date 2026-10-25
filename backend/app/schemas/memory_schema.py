from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MemoryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    memory_date: datetime | None = None


class MemoryUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    memory_date: datetime | None = None


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group_id: UUID
    created_by: UUID
    title: str
    description: str | None
    memory_date: datetime | None
    created_at: datetime