import uuid

from pydantic import BaseModel, Field, model_validator

from app.models.location import LocationType


class PointGeometry(BaseModel):
    """GeoJSON-style point for API input/output."""
    type: str = "Point"
    coordinates: list[float] = Field(..., min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_coordinates(self) -> "PointGeometry":
        lng, lat = self.coordinates
        if not (-180 <= lng <= 180):
            raise ValueError("longitude must be between -180 and 180")
        if not (-90 <= lat <= 90):
            raise ValueError("latitude must be between -90 and 90")
        return self


class LocationCreate(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=255, pattern=r"^[a-z0-9-]+$")
    location_type: LocationType
    country: str | None = Field(None, max_length=100)
    region: str | None = Field(None, max_length=255)
    description: str | None = None
    # Accepts GeoJSON coordinates [lng, lat] — stored as PostGIS POINT(lng lat)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class LocationRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    location_type: LocationType
    country: str | None
    region: str | None
    description: str | None
    latitude: float | None = None
    longitude: float | None = None

    model_config = {"from_attributes": True}
