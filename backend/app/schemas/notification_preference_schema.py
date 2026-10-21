from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationPreferenceUpdate(BaseModel):
    enabled: bool = True
    daily_drop_enabled: bool = True
    group_activity_enabled: bool = True
    quiet_hours_start: int | None = None
    quiet_hours_end: int | None = None


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    enabled: bool
    daily_drop_enabled: bool
    group_activity_enabled: bool
    quiet_hours_start: int | None
    quiet_hours_end: int | None
    created_at: datetime
    updated_at: datetime