from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    bio: str | None
    display_name: str

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserUpdate(BaseModel):
    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    bio: str | None = Field(
        default=None,
        max_length=500,
    )

    @model_validator(mode="after")
    def validate_update(self):
        if self.display_name is None and self.bio is None:
            raise ValueError("At least one profile field must be provided")

        return self
