from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecommendationCreate(BaseModel):
    recommendation_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    source: str = Field(min_length=1, max_length=100)
    description: str | None = None


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    recommendation_type: str
    title: str
    description: str | None
    source: str
    created_at: datetime