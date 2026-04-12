import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.group import GroupType, JoinPolicy, MemberRole


class GroupCreate(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    group_type: GroupType
    is_public: bool = True
    join_policy: JoinPolicy = JoinPolicy.open


class GroupUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    is_public: bool | None = None
    join_policy: JoinPolicy | None = None


class GroupRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    group_type: GroupType
    owner_id: uuid.UUID
    is_public: bool
    join_policy: JoinPolicy
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GroupSummary(BaseModel):
    """Minimal view embedded in sighting/membership responses."""
    id: uuid.UUID
    name: str
    slug: str
    group_type: GroupType

    model_config = {"from_attributes": True}


class GroupMembershipRead(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    user_id: uuid.UUID
    role: MemberRole
    joined_at: datetime

    model_config = {"from_attributes": True}
