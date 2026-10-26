from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MemoryMediaCreate(BaseModel):
    media_id: UUID


class MemoryMediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    memory_id: UUID
    media_id: UUID
    created_at: datetime