"""
Sighting — primary observation record.

Darwin Core mapping (DwC: Occurrence):
  id                  → occurrenceID
  observed_at         → eventDate
  geometry (lat/lng)  → decimalLatitude / decimalLongitude
  species.scientific_name → scientificName
  user (display_name) → recordedBy
  count               → individualCount
  verified            → occurrenceStatus (present/absent proxy)
"""

import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDMixin


class Visibility(str, enum.Enum):
    private = "private"
    group = "group"
    public = "public"


class Sighting(UUIDMixin, Base):
    __tablename__ = "sightings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    species_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("species.id", ondelete="RESTRICT"),
        nullable=False,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    # PostGIS POINT (SRID 4326 — WGS84). GIST index added in __table_args__.
    geometry = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    location_description: Mapped[str | None] = mapped_column(Text)
    count: Mapped[int | None] = mapped_column(Integer)
    behaviour_notes: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, name="visibility"),
        nullable=False,
        default=Visibility.public,
    )
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="sightings", foreign_keys=[user_id]
    )
    verifier: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[verified_by]
    )
    group: Mapped["Group | None"] = relationship(back_populates="sightings")  # noqa: F821
    species: Mapped["Species"] = relationship(back_populates="sightings")  # noqa: F821
    media: Mapped[list["Media"]] = relationship(back_populates="sighting")  # noqa: F821
    ingest_records: Mapped[list["IngestRecord"]] = relationship(  # noqa: F821
        back_populates="canonical_sighting"
    )

    __table_args__ = (
        Index("ix_sightings_user_id", "user_id"),
        Index("ix_sightings_group_id", "group_id"),
        Index("ix_sightings_species_id", "species_id"),
        Index("ix_sightings_observed_at", "observed_at"),
        Index("ix_sightings_geometry", "geometry", postgresql_using="gist"),
    )
