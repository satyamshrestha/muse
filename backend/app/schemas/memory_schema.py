from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MemoryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    memory_date: datetime | None = None
    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class MemoryUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    memory_date: datetime | None = None
    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group_id: UUID
    created_by: UUID
    title: str
    description: str | None
    memory_date: datetime | None
    created_at: datetime