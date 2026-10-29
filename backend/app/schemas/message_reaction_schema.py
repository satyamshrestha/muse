from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageReactionCreate(BaseModel):
    reaction: str = Field(min_length=1, max_length=50)


class MessageReactionUpdate(BaseModel):
    reaction: str = Field(min_length=1, max_length=50)


class MessageReactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    message_id: UUID
    user_id: UUID
    reaction: str
    created_at: datetime