import enum
import uuid

from sqlalchemy import Enum, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDMixin

try:
    from geoalchemy2 import Geometry
    _HAS_GEOALCHEMY = True
except ImportError:
    _HAS_GEOALCHEMY = False


class UserRole(str, enum.Enum):
    observer = "observer"
    curator = "curator"
    admin = "admin"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    auth_provider: Mapped[str | None] = mapped_column(String(50))
    auth_provider_id: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(Text)
    location_home = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=True
    )
    avatar_url: Mapped[str | None] = mapped_column(String(2048))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"),
        nullable=False,
        default=UserRole.observer,
    )

    # Relationships
    sightings: Mapped[list["Sighting"]] = relationship(  # noqa: F821
        back_populates="user", foreign_keys="Sighting.user_id"
    )
    group_memberships: Mapped[list["GroupMembership"]] = relationship(  # noqa: F821
        back_populates="user"
    )
    owned_groups: Mapped[list["Group"]] = relationship(  # noqa: F821
        back_populates="owner"
    )

    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_auth_provider_id", "auth_provider_id"),
        Index("ix_users_location_home", "location_home", postgresql_using="gist"),
    )
