import uuid

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sighting import Sighting, Visibility
from app.models.species import Species
from app.schemas.common import PaginatedResponse
from app.schemas.sighting import SightingCreate, SightingDetail, SightingRead


async def get_sightings_list(
    db: AsyncSession,
    *,
    species_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    group_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 20,
) -> PaginatedResponse[SightingRead]:
    query = select(Sighting).where(Sighting.visibility == Visibility.public)

    if species_id:
        query = query.where(Sighting.species_id == species_id)
    if user_id:
        query = query.where(Sighting.user_id == user_id)
    if group_id:
        query = query.where(Sighting.group_id == group_id)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    data_query = query.add_columns(
        func.ST_Y(Sighting.geometry).label("latitude"),
        func.ST_X(Sighting.geometry).label("longitude"),
    )
    result = await db.execute(
        data_query.order_by(Sighting.observed_at.desc()).offset(skip).limit(limit)
    )
    rows = result.all()

    return PaginatedResponse(
        items=[
            SightingRead.model_validate(s).model_copy(update={"latitude": lat, "longitude": lng})
            for s, lat, lng in rows
        ],
        total=total,
        limit=limit,
        offset=skip,
    )


async def get_nearby_sightings(
    db: AsyncSession,
    *,
    latitude: float,
    longitude: float,
    radius_km: float,
) -> list[SightingRead]:
    # PostGIS argument order: ST_MakePoint(longitude, latitude)
    # ST_DWithin distance argument is in metres when using geography cast
    radius_m = radius_km * 1000
    point = func.ST_MakePoint(longitude, latitude)

    result = await db.execute(
        select(Sighting)
        .where(
            Sighting.visibility == Visibility.public,
            func.ST_DWithin(
                func.ST_GeogFromWKB(Sighting.geometry),
                func.ST_GeogFromWKB(func.ST_SetSRID(point, 4326)),
                radius_m,
            ),
        )
        .order_by(
            func.ST_Distance(
                func.ST_GeogFromWKB(Sighting.geometry),
                func.ST_GeogFromWKB(func.ST_SetSRID(point, 4326)),
            )
        )
        .add_columns(
            func.ST_Y(Sighting.geometry).label("latitude"),
            func.ST_X(Sighting.geometry).label("longitude"),
        )
        .limit(100)
    )
    return [
        SightingRead.model_validate(s).model_copy(update={"latitude": lat, "longitude": lng})
        for s, lat, lng in result.all()
    ]


async def get_sighting_by_id(
    db: AsyncSession, sighting_id: uuid.UUID
) -> SightingDetail:
    result = await db.execute(
        select(Sighting)
        .where(
            Sighting.id == sighting_id,
            Sighting.visibility == Visibility.public,
        )
        .options(
            selectinload(Sighting.species),
            selectinload(Sighting.user),
        )
        .add_columns(
            func.ST_Y(Sighting.geometry).label("latitude"),
            func.ST_X(Sighting.geometry).label("longitude"),
        )
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Sighting not found")
    sighting, lat, lng = row
    return SightingDetail.model_validate(sighting).model_copy(update={"latitude": lat, "longitude": lng})


async def create_sighting(
    db: AsyncSession,
    payload: SightingCreate,
    *,
    user_id: uuid.UUID,
) -> SightingRead:
    # Geometry constructed server-side from validated lat/lng.
    # PostGIS ST_MakePoint takes (longitude, latitude) — never swap.
    geometry = func.ST_SetSRID(
        func.ST_MakePoint(payload.longitude, payload.latitude),
        4326,
    )
    sighting = Sighting(
        user_id=user_id,
        group_id=payload.group_id,
        species_id=payload.species_id,
        observed_at=payload.observed_at,
        geometry=geometry,
        location_description=payload.location_description,
        count=payload.count,
        behaviour_notes=payload.behaviour_notes,
        visibility=payload.visibility,
    )
    db.add(sighting)
    await db.commit()
    await db.refresh(sighting)

    try:
        from app.search.indexes import index_sighting
        species_result = await db.execute(select(Species).where(Species.id == sighting.species_id))
        species = species_result.scalar_one_or_none()
        await index_sighting(sighting, species, payload.latitude, payload.longitude)
    except Exception:
        import logging
        logging.getLogger(__name__).warning("Search indexing failed for sighting %s", sighting.id, exc_info=True)

    return SightingRead.model_validate(sighting)


async def get_sightings_by_ids(
    db: AsyncSession,
    sighting_ids: list[uuid.UUID],
) -> list[SightingRead]:
    """Fetch sightings by explicit ID list, preserving search relevance order."""
    if not sighting_ids:
        return []
    result = await db.execute(
        select(Sighting)
        .where(
            Sighting.id.in_(sighting_ids),
            Sighting.visibility == Visibility.public,
        )
        .add_columns(
            func.ST_Y(Sighting.geometry).label("latitude"),
            func.ST_X(Sighting.geometry).label("longitude"),
        )
    )
    rows = {str(s.id): (s, lat, lng) for s, lat, lng in result.all()}
    # Return in search-result order (IDs came from Azure AI Search ranking)
    return [
        SightingRead.model_validate(rows[str(sid)][0]).model_copy(
            update={"latitude": rows[str(sid)][1], "longitude": rows[str(sid)][2]}
        )
        for sid in sighting_ids
        if str(sid) in rows
    ]


async def search_sightings_db(
    db: AsyncSession,
    *,
    q: str | None = None,
    visibility: Visibility = Visibility.public,
    skip: int = 0,
    limit: int = 20,
) -> PaginatedResponse[SightingRead]:
    """DB ilike fallback when Azure AI Search is unavailable."""
    query = select(Sighting).where(Sighting.visibility == visibility)

    if q:
        pattern = f"%{q}%"
        query = query.where(
            or_(
                Sighting.behaviour_notes.ilike(pattern),
                Sighting.location_description.ilike(pattern),
            )
        )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    data_query = query.add_columns(
        func.ST_Y(Sighting.geometry).label("latitude"),
        func.ST_X(Sighting.geometry).label("longitude"),
    )
    result = await db.execute(
        data_query.order_by(Sighting.observed_at.desc()).offset(skip).limit(limit)
    )
    rows = result.all()

    return PaginatedResponse(
        items=[
            SightingRead.model_validate(s).model_copy(update={"latitude": lat, "longitude": lng})
            for s, lat, lng in rows
        ],
        total=total,
        limit=limit,
        offset=skip,
    )
