# IMPORTANT: IngestRecord rows are the raw preservation layer.
# NEVER add delete logic to this model.
# Raw payload must always be preserved alongside any canonical mapping.
# See CLAUDE.md: Three-layer ingest model and the "MHR PDF problem".

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDMixin


class SourceFormat(str, enum.Enum):
    dwc = "dwc"
    csv = "csv"
    shapefile = "shapefile"
    json = "json"
    pdf = "pdf"
    api = "api"


class IngestRecord(UUIDMixin, Base):
    __tablename__ = "ingest_records"

    source_format: Mapped[SourceFormat] = mapped_column(
        Enum(SourceFormat, name="sourceformat"),
        nullable=False,
    )
    source_system: Mapped[str | None] = mapped_column(String(255))
    source_reference: Mapped[str | None] = mapped_column(String(512))
    # Original data — immutable after write.
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    mapped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mapping_confidence: Mapped[float | None] = mapped_column(Float)
    mapping_notes: Mapped[str | None] = mapped_column(Text)
    canonical_sighting_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sightings.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    submitter: Mapped["User"] = relationship(foreign_keys=[submitted_by])  # noqa: F821
    canonical_sighting: Mapped["Sighting | None"] = relationship(  # noqa: F821
        back_populates="ingest_records", foreign_keys=[canonical_sighting_id]
    )

    __table_args__ = (
        Index("ix_ingest_records_submitted_by", "submitted_by"),
        Index("ix_ingest_records_canonical_sighting_id", "canonical_sighting_id"),
    )
