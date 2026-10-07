from pydantic import BaseModel, Field


class NotificationPreferenceInput(BaseModel):
    enabled: bool = True
    daily_drop_enabled: bool = True
    group_activity_enabled: bool = True
    quiet_hours_start: int | None = Field(
        default=None,
        ge=0,
        le=23,
    )
    quiet_hours_end: int | None = Field(
        default=None,
        ge=0,
        le=23,
    )


class PersonalizationUpdate(BaseModel):
    interests: list[str] = Field(default_factory=list)
    preferences: dict[str, str] = Field(default_factory=dict)
    feature_preferences: dict[str, str] = Field(default_factory=dict)
    notifications: NotificationPreferenceInput


class PersonalizationResponse(BaseModel):
    configuration_id: str | None
    configuration_name: str | None
    interests: list[str]
    preferences: dict[str, str]
    feature_preferences: dict[str, str]
    notifications: NotificationPreferenceInput | None