from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanParticipantCreate(BaseModel):
    user_id: UUID


class PlanParticipantRespond(BaseModel):
    status: Literal["accepted", "declined"]


class PlanParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    user_id: UUID
    status: str
    created_at: datetime