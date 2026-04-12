import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.media import MediaStatus, MediaType


class MediaRead(BaseModel):
    id: uuid.UUID
    sighting_id: uuid.UUID | None
    user_id: uuid.UUID
    status: MediaStatus
    cdn_url: str | None
    media_type: MediaType
    file_size: int | None
    mime_type: str | None
    observed_at_device: datetime | None
    exif_lat: float | None
    exif_lng: float | None
    # gps_stripped indicates whether GPS was removed from the CDN copy for privacy
    gps_stripped: bool
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class MediaCreate(BaseModel):
    sighting_id: uuid.UUID | None = None
    media_type: MediaType
    mime_type: str | None = Field(None, max_length=100)
    # EXIF data captured client-side — immutable after first write
    observed_at_device: datetime | None = None
    exif_lat: float | None = Field(None, ge=-90, le=90)
    exif_lng: float | None = Field(None, ge=-180, le=180)
    exif_data: dict[str, Any] | None = None


class MediaAttach(BaseModel):
    """Attach a draft media record to a sighting."""
    sighting_id: uuid.UUID
