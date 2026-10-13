from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeviceRegisterRequest(BaseModel):
    device_token: str = Field(min_length=1, max_length=500)
    platform: str = Field(min_length=1, max_length=50)


class DevicePlatformUpdate(BaseModel):
    platform: str = Field(min_length=1, max_length=50)


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    platform: str
    created_at: datetime
    updated_at: datetime