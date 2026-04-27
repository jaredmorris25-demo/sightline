import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.species import Species
from app.schemas.common import PaginatedResponse
from app.schemas.species import SpeciesCreate, SpeciesRead, SpeciesSummary


async def get_species_list(
    db: AsyncSession,
    *,
    kingdom: str | None = None,
    family: str | None = None,
    conservation_status: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> PaginatedResponse[SpeciesRead]:
    query = select(Species)

    if kingdom:
        query = query.where(Species.kingdom.ilike(f"%{kingdom}%"))
    if family:
        query = query.where(Species.family.ilike(f"%{family}%"))
    if conservation_status:
        query = query.where(Species.conservation_status == conservation_status)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(query.order_by(Species.scientific_name).offset(skip).limit(limit))
    items = result.scalars().all()

    return PaginatedResponse(
        items=[SpeciesRead.model_validate(s) for s in items],
        total=total,
        limit=limit,
        offset=skip,
    )


async def search_species(
    db: AsyncSession,
    *,
    q: str,
) -> list[SpeciesSummary]:
    pattern = f"%{q}%"
    result = await db.execute(
        select(Species)
        .where(
            Species.common_name.ilike(pattern) | Species.scientific_name.ilike(pattern)
        )
        .order_by(Species.scientific_name)
        .limit(50)
    )
    return [SpeciesSummary.model_validate(s) for s in result.scalars().all()]


async def get_species_by_id(db: AsyncSession, species_id: uuid.UUID) -> SpeciesRead:
    result = await db.execute(select(Species).where(Species.id == species_id))
    species = result.scalar_one_or_none()
    if species is None:
        raise HTTPException(status_code=404, detail="Species not found")
    return SpeciesRead.model_validate(species)


async def create_species(db: AsyncSession, payload: SpeciesCreate) -> SpeciesRead:
    species = Species(
        scientific_name=payload.scientific_name,
        common_name=payload.common_name,
        kingdom=payload.kingdom,
        phylum=payload.phylum,
        class_name=payload.class_name,
        order_name=payload.order_name,
        family=payload.family,
        genus=payload.genus,
        inaturalist_id=payload.inaturalist_id,
        gbif_id=payload.gbif_id,
        ala_id=payload.ala_id,
        conservation_status=payload.conservation_status,
        description=payload.description,
    )
    db.add(species)
    await db.commit()
    await db.refresh(species)

    try:
        from app.search.indexes import index_species
        await index_species(species)
    except Exception:
        import logging
        logging.getLogger(__name__).warning("Search indexing failed for species %s", species.id, exc_info=True)

    return SpeciesRead.model_validate(species)
