import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.media import MediaStatus, MediaType


class MediaPresignRequest(BaseModel):
    filename: str
    content_type: Literal["image/jpeg", "image/png", "image/heic", "video/mp4"]
    sighting_id: uuid.UUID | None = None


class MediaPresignResponse(BaseModel):
    media_id: uuid.UUID
    upload_url: str
    blob_path: str
    expires_at: datetime


class MediaRead(BaseModel):
    id: uuid.UUID
    sighting_id: uuid.UUID | None
    user_id: uuid.UUID
    status: MediaStatus
    blob_url: str | None
    cdn_url: str | None
    media_type: MediaType
    file_size: int | None
    mime_type: str | None
    observed_at_device: datetime | None
    exif_lat: float | None
    exif_lng: float | None
    gps_stripped: bool
    uploaded_at: datetime
    synced_at: datetime | None

    model_config = {"from_attributes": True}
