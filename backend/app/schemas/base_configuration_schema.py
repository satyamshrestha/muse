from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseConfigurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    interests: list[str]
    preferences: dict
    created_at: datetime