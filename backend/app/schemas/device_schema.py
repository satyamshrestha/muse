from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class DeviceRegisterRequest(BaseModel):
    device_token: str = Field(min_length=1, max_length=500)
    platform: str = Field(min_length=1, max_length=50)

    @field_validator("device_token", "platform")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be blank.")
        return value


class DevicePlatformUpdate(BaseModel):
    platform: str = Field(min_length=1, max_length=50)

    @field_validator("platform")
    @classmethod
    def reject_blank_platform(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Platform cannot be blank.")
        return value


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    platform: str
    created_at: datetime
    updated_at: datetime