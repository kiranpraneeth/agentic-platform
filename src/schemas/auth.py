"""Authentication schemas."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    email: str
    role: str

    model_config = {"from_attributes": True}
