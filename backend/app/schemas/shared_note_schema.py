from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SharedNoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class SharedNoteUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class SharedNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group_id: UUID
    created_by: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime