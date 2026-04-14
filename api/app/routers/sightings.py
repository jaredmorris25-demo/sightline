import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.user_context import get_current_user_id
from app.db.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.sighting import SightingCreate, SightingDetail, SightingRead
from app.services import sighting_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[SightingRead])
async def list_sightings(
    species_id: uuid.UUID | None = Query(None),
    user_id: uuid.UUID | None = Query(None),
    group_id: uuid.UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await sighting_service.get_sightings_list(
        db,
        species_id=species_id,
        user_id=user_id,
        group_id=group_id,
        skip=skip,
        limit=limit,
    )


@router.get("/nearby", response_model=list[SightingRead])
async def nearby_sightings(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(..., gt=0, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await sighting_service.get_nearby_sightings(
        db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )


@router.get("/{sighting_id}", response_model=SightingDetail)
async def get_sighting(
    sighting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await sighting_service.get_sighting_by_id(db, sighting_id)


@router.post("/", response_model=SightingRead, status_code=201)
async def create_sighting(
    payload: SightingCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await sighting_service.create_sighting(
        db,
        payload,
        user_id=user_id,
    )
