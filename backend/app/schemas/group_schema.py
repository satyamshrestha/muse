from uuid import UUID

from pydantic import BaseModel, Field


class GroupCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )


class GroupResponse(BaseModel):
    id: UUID
    name: str