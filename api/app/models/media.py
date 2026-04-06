import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDMixin


class MediaType(str, enum.Enum):
    photo = "photo"
    audio = "audio"
    video = "video"


class MediaStatus(str, enum.Enum):
    draft = "draft"
    attached = "attached"
    processing = "processing"
    ready = "ready"


class Media(UUIDMixin, Base):
    __tablename__ = "media"

    sighting_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sightings.id", ondelete="SET NULL"),
        nullable=True,  # nullable until attached from draft
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[MediaStatus] = mapped_column(
        Enum(MediaStatus, name="mediastatus"),
        nullable=False,
        default=MediaStatus.draft,
    )
    blob_url: Mapped[str | None] = mapped_column(String(2048))
    cdn_url: Mapped[str | None] = mapped_column(String(2048))
    media_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="mediatype"),
        nullable=False,
    )
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    # Full EXIF payload preserved as JSONB — never modified after write.
    exif_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # Capture timestamp from EXIF — never overwritten once set.
    observed_at_device: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exif_lat: Mapped[float | None] = mapped_column(Float)
    exif_lng: Mapped[float | None] = mapped_column(Float)
    # True once GPS data has been stripped from the CDN copy for privacy.
    gps_stripped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    sighting: Mapped["Sighting | None"] = relationship(back_populates="media")  # noqa: F821

    __table_args__ = (
        Index("ix_media_sighting_id", "sighting_id"),
        Index("ix_media_user_id", "user_id"),
    )
