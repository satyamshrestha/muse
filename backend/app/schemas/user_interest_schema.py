from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserInterestReplace(BaseModel):
    interests: list[str] = Field(max_length=50)

    @field_validator("interests")
    @classmethod
    def validate_interests(cls, values: list[str]) -> list[str]:
        normalized = []

        for value in values:
            value = value.strip()

            if not value:
                raise ValueError("Interests cannot be empty.")

            if len(value) > 100:
                raise ValueError(
                    "Each interest must be at most 100 characters."
                )

            normalized.append(value)

        return normalized


class UserInterestItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    interest: str
    created_at: datetime


class UserInterestResponse(BaseModel):
    interests: list[UserInterestItem]