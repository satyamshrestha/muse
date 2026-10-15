from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    remind_at: datetime

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Reminder title cannot be empty.")
        return value

    @field_validator("remind_at")
    @classmethod
    def validate_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Reminder time must include a timezone.")
        return value


class ReminderUpdate(ReminderCreate):
    pass


class ReminderCompletionUpdate(BaseModel):
    completed: bool


class ReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    remind_at: datetime
    completed: bool
    created_at: datetime