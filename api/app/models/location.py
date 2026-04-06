"""
Location — named geographic places.

Darwin Core mapping (DwC: Location):
  id          → locationID
  name        → locality
  region      → stateProvince
  country     → country
  geometry    → decimalLatitude / decimalLongitude (point)
                or footprintWKT (polygon)
  (datum)     → geodeticDatum = 'EPSG:4326'
"""

import enum

from geoalchemy2 import Geometry
from sqlalchemy import Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDMixin


class LocationType(str, enum.Enum):
    park = "park"
    reserve = "reserve"
    marine = "marine"
    urban = "urban"
    rural = "rural"


class Location(UUIDMixin, Base):
    __tablename__ = "locations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # PostGIS geometry supporting both POINT and POLYGON (SRID 4326 — WGS84).
    # GIST index added in __table_args__.
    geometry = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326),
        nullable=False,
    )
    location_type: Mapped[LocationType] = mapped_column(
        Enum(LocationType, name="locationtype"),
        nullable=False,
    )
    country: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_locations_slug", "slug"),
        Index("ix_locations_geometry", "geometry", postgresql_using="gist"),
    )
