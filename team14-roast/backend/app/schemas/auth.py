"""Auth request/response schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Payload for account registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value: str) -> str:
        """Reject passwords exceeding bcrypt's 72-byte limit."""
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes")
        return value


class LoginRequest(BaseModel):
    """Payload for email/password login."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RefreshRequest(BaseModel):
    """Payload carrying a refresh token."""

    refresh_token: str


class UpdateProfileRequest(BaseModel):
    """Payload for updating the current user's profile."""

    full_name: str = Field(min_length=1, max_length=100)


class UserOut(BaseModel):
    """Public user representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    oauth_provider: str | None
    created_at: datetime


class TokenPair(BaseModel):
    """Access + refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(TokenPair):
    """Token pair plus the authenticated user."""

    user: UserOut
