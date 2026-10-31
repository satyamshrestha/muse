from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BehavioralSignalCreate(BaseModel):
    signal_type: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=255)


class BehavioralSignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    signal_type: str
    value: str
    created_at: datetime