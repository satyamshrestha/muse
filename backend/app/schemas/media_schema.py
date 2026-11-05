from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MediaCreate(BaseModel):
    object_key: str = Field(min_length=1, max_length=500)
    media_type: str = Field(min_length=1, max_length=50)
    mime_type: str = Field(min_length=1, max_length=100)


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    uploaded_by: UUID
    object_key: str
    media_type: str
    mime_type: str
    created_at: datetime