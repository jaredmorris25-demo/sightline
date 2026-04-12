import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SpeciesBase(BaseModel):
    scientific_name: str = Field(..., max_length=255)
    common_name: str | None = Field(None, max_length=255)
    kingdom: str | None = Field(None, max_length=100)
    phylum: str | None = Field(None, max_length=100)
    class_name: str | None = Field(None, max_length=100, alias="class")
    order_name: str | None = Field(None, max_length=100, alias="order")
    family: str | None = Field(None, max_length=100)
    genus: str | None = Field(None, max_length=100)
    inaturalist_id: str | None = Field(None, max_length=100)
    gbif_id: str | None = Field(None, max_length=100)
    ala_id: str | None = Field(None, max_length=100)
    conservation_status: str | None = Field(None, max_length=20)
    description: str | None = None

    model_config = {"populate_by_name": True}


class SpeciesCreate(SpeciesBase):
    pass


class SpeciesUpdate(BaseModel):
    common_name: str | None = Field(None, max_length=255)
    conservation_status: str | None = Field(None, max_length=20)
    description: str | None = None
    inaturalist_id: str | None = Field(None, max_length=100)
    gbif_id: str | None = Field(None, max_length=100)
    ala_id: str | None = Field(None, max_length=100)


class SpeciesRead(SpeciesBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class SpeciesSummary(BaseModel):
    """Minimal view embedded in sighting responses."""
    id: uuid.UUID
    scientific_name: str
    common_name: str | None

    model_config = {"from_attributes": True}
