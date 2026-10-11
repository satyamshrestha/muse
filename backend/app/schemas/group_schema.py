from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class GroupResponse(BaseModel):
    id: UUID
    name: str


class GroupMemberResponse(BaseModel):
    id: UUID
    display_name: str


class GroupInvitationCreateResponse(BaseModel):
    token: str
    expires_at: datetime


class GroupInvitationRedeem(BaseModel):
    token: str = Field(min_length=20, max_length=200)