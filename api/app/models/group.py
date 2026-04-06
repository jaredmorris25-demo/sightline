import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin


class GroupType(str, enum.Enum):
    cls = "class"
    team = "team"
    org = "org"
    campaign = "campaign"
    open = "open"


class JoinPolicy(str, enum.Enum):
    open = "open"
    invite = "invite"
    approval = "approval"


class MemberRole(str, enum.Enum):
    member = "member"
    moderator = "moderator"
    admin = "admin"


class Group(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    group_type: Mapped[GroupType] = mapped_column(
        Enum(GroupType, name="grouptype", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    join_policy: Mapped[JoinPolicy] = mapped_column(
        Enum(JoinPolicy, name="joinpolicy"),
        nullable=False,
        default=JoinPolicy.open,
    )

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="owned_groups")  # noqa: F821
    memberships: Mapped[list["GroupMembership"]] = relationship(back_populates="group")
    sightings: Mapped[list["Sighting"]] = relationship(back_populates="group")  # noqa: F821

    __table_args__ = (
        Index("ix_groups_slug", "slug"),
    )


class GroupMembership(UUIDMixin, Base):
    __tablename__ = "group_memberships"

    group_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, name="memberrole"),
        nullable=False,
        default=MemberRole.member,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    group: Mapped["Group"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="group_memberships")  # noqa: F821

    __table_args__ = (
        Index("ix_group_memberships_group_id", "group_id"),
        Index("ix_group_memberships_user_id", "user_id"),
    )
