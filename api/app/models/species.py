"""
Species — taxonomic reference entity.

Darwin Core mapping (DwC: Taxon):
  id               → taxonID
  scientific_name  → scientificName
  kingdom          → kingdom
  phylum           → phylum
  class_name       → class  (NOTE: 'class' is reserved in Python — stored as class_name)
  order_name       → order  (NOTE: 'order' is reserved in Python — stored as order_name)
  family           → family
  genus            → genus
  common_name      → vernacularName
  conservation_status → (no direct DwC equivalent; use IUCN codes)
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDMixin


class Species(UUIDMixin, Base):
    __tablename__ = "species"

    common_name: Mapped[str | None] = mapped_column(String(255))
    scientific_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    kingdom: Mapped[str | None] = mapped_column(String(100))
    phylum: Mapped[str | None] = mapped_column(String(100))
    class_name: Mapped[str | None] = mapped_column("class", String(100))
    order_name: Mapped[str | None] = mapped_column("order", String(100))
    family: Mapped[str | None] = mapped_column(String(100))
    genus: Mapped[str | None] = mapped_column(String(100))
    inaturalist_id: Mapped[str | None] = mapped_column(String(100))
    gbif_id: Mapped[str | None] = mapped_column(String(100))
    ala_id: Mapped[str | None] = mapped_column(String(100))
    conservation_status: Mapped[str | None] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    sightings: Mapped[list["Sighting"]] = relationship(back_populates="species")  # noqa: F821

    __table_args__ = (
        Index("ix_species_scientific_name", "scientific_name"),
    )
