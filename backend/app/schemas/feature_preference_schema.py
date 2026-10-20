from pydantic import BaseModel, ConfigDict, Field


class FeaturePreferenceReplace(BaseModel):
    feature_preferences: dict[str, str] = Field(default_factory=dict)


class FeaturePreferenceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feature: str
    preference: str


class FeaturePreferenceResponse(BaseModel):
    feature_preferences: list[FeaturePreferenceItem]