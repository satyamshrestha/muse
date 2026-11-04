from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecommendationInteractionCreate(BaseModel):
    recommendation_id: UUID
    interaction_type: str = Field(min_length=1, max_length=100)


class RecommendationInteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    recommendation_id: UUID
    interaction_type: str
    created_at: datetime