import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.ingest import SourceFormat


class IngestRecordCreate(BaseModel):
    source_format: SourceFormat
    source_system: str | None = Field(None, max_length=255)
    source_reference: str | None = Field(None, max_length=512)
    raw_payload: dict[str, Any]
    group_id: uuid.UUID | None = None


class IngestRecordRead(BaseModel):
    id: uuid.UUID
    source_format: SourceFormat
    source_system: str | None
    source_reference: str | None
    group_id: uuid.UUID | None
    submitted_by: uuid.UUID
    submitted_at: datetime
    mapped_at: datetime | None
    mapping_confidence: float | None
    mapping_notes: str | None
    canonical_sighting_id: uuid.UUID | None

    model_config = {"from_attributes": True}
