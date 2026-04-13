import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    display_name: str = Field(..., max_length=255)
    bio: str | None = None
    avatar_url: str | None = Field(None, max_length=2048)


class UserRead(UserBase):
    id: uuid.UUID
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    """Reduced view — safe to expose in sighting/group responses."""
    id: uuid.UUID
    display_name: str
    avatar_url: str | None
    role: UserRole

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, max_length=255)
    bio: str | None = None
    avatar_url: str | None = Field(None, max_length=2048)
