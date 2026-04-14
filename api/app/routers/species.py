import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.user_context import get_current_user_id
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.species import SpeciesCreate, SpeciesRead, SpeciesSummary
from app.services import species_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[SpeciesRead])
async def list_species(
    kingdom: str | None = Query(None),
    family: str | None = Query(None),
    conservation_status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await species_service.get_species_list(
        db,
        kingdom=kingdom,
        family=family,
        conservation_status=conservation_status,
        skip=skip,
        limit=limit,
    )


@router.get("/search", response_model=list[SpeciesSummary])
async def search_species(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
):
    return await species_service.search_species(db, q=q)


@router.get("/{species_id}", response_model=SpeciesRead)
async def get_species(
    species_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await species_service.get_species_by_id(db, species_id)


@router.post("/", response_model=SpeciesRead, status_code=201)
async def create_species(
    payload: SpeciesCreate,
    db: AsyncSession = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
):
    return await species_service.create_species(db, payload)
