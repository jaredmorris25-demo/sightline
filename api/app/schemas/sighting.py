import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator

from app.models.sighting import Visibility
from app.schemas.species import SpeciesSummary
from app.schemas.user import UserPublic


class SightingCreate(BaseModel):
    species_id: uuid.UUID
    group_id: uuid.UUID | None = None
    observed_at: datetime
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_description: str | None = None
    count: int | None = Field(None, ge=1)
    behaviour_notes: str | None = None
    visibility: Visibility = Visibility.public

    @model_validator(mode="after")
    def observed_at_must_not_be_future(self) -> "SightingCreate":
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware (include UTC offset)")
        if self.observed_at > datetime.now(timezone.utc):
            raise ValueError("observed_at cannot be in the future")
        return self


class SightingUpdate(BaseModel):
    observed_at: datetime | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    location_description: str | None = None
    count: int | None = Field(None, ge=1)
    behaviour_notes: str | None = None
    visibility: Visibility | None = None


class SightingRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    group_id: uuid.UUID | None
    species_id: uuid.UUID
    observed_at: datetime
    latitude: float | None = None
    longitude: float | None = None
    location_description: str | None
    count: int | None
    behaviour_notes: str | None
    visibility: Visibility
    verified: bool
    verified_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SightingDetail(SightingRead):
    """Full sighting response with embedded related objects."""
    species: SpeciesSummary | None = None
    user: UserPublic | None = None

    model_config = {"from_attributes": True}
