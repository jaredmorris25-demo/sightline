import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.sighting import Visibility
from app.schemas.common import PaginatedResponse
from app.schemas.sighting import SightingRead
from app.schemas.species import SpeciesSummary
from app.search.client import get_search_client
from app.services import sighting_service, species_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/species", response_model=PaginatedResponse[SpeciesSummary])
async def search_species(
    q: str | None = Query(None, description="Full-text search query"),
    kingdom: str | None = Query(None),
    conservation_status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    client = get_search_client(settings.azure_search_index_species)
    if client is not None:
        try:
            return await _azure_search_species(client, q, kingdom, conservation_status, skip, limit)
        except Exception:
            logger.warning("Azure species search failed, falling back to database", exc_info=True)

    # DB fallback — existing ilike search wrapped in PaginatedResponse
    items = await species_service.search_species(db, q=q or "")
    if kingdom:
        items = [s for s in items if s.common_name and kingdom.lower() in (s.common_name or "").lower()]
    return PaginatedResponse(items=items[skip: skip + limit], total=len(items), limit=limit, offset=skip)


async def _azure_search_species(
    client,
    q: str | None,
    kingdom: str | None,
    conservation_status: str | None,
    skip: int,
    limit: int,
) -> PaginatedResponse[SpeciesSummary]:
    filters = []
    if kingdom:
        filters.append(f"kingdom eq '{kingdom}'")
    if conservation_status:
        filters.append(f"conservation_status eq '{conservation_status}'")
    filter_str = " and ".join(filters) if filters else None

    def _search() -> tuple[list[SpeciesSummary], int]:
        results = client.search(
            search_text=f"{q}~" if q else "*",
            query_type="full",
            filter=filter_str,
            select=["id", "common_name", "scientific_name"],
            skip=skip,
            top=limit,
            include_total_count=True,
        )
        docs = [
            SpeciesSummary(
                id=uuid.UUID(doc["id"]),
                common_name=doc.get("common_name"),
                scientific_name=doc["scientific_name"],
            )
            for doc in results
        ]
        return docs, results.get_count() or len(docs)

    items, total = await asyncio.to_thread(_search)
    return PaginatedResponse(items=items, total=total, limit=limit, offset=skip)


@router.get("/sightings", response_model=PaginatedResponse[SightingRead])
async def search_sightings(
    q: str | None = Query(None, description="Full-text search query"),
    visibility: str = Query("public", description="Filter by visibility"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    vis = Visibility(visibility)

    client = get_search_client(settings.azure_search_index_sightings)
    if client is not None:
        try:
            return await _azure_search_sightings(client, db, q, vis, skip, limit)
        except Exception:
            logger.warning("Azure sightings search failed, falling back to database", exc_info=True)

    return await sighting_service.search_sightings_db(db, q=q, visibility=vis, skip=skip, limit=limit)


async def _azure_search_sightings(
    client,
    db: AsyncSession,
    q: str | None,
    visibility: Visibility,
    skip: int,
    limit: int,
) -> PaginatedResponse[SightingRead]:
    filter_str = f"visibility eq '{visibility.value}'"

    def _search() -> tuple[list[uuid.UUID], int]:
        results = client.search(
            search_text=f"{q}~" if q else "*",
            query_type="full",
            filter=filter_str,
            select=["id"],
            skip=skip,
            top=limit,
            include_total_count=True,
        )
        ids = [uuid.UUID(doc["id"]) for doc in results]
        return ids, results.get_count() or 0

    sighting_ids, total = await asyncio.to_thread(_search)
    items = await sighting_service.get_sightings_by_ids(db, sighting_ids)
    return PaginatedResponse(items=items, total=total, limit=limit, offset=skip)
