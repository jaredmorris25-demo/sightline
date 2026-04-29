import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.user_context import get_current_user_id
from app.db.session import get_db
from app.schemas.media_upload import MediaPresignRequest, MediaPresignResponse, MediaRead
from app.services import media_service

router = APIRouter()


@router.post("/presign", response_model=MediaPresignResponse, status_code=201)
async def presign_upload(
    payload: MediaPresignRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    media = await media_service.create_media_draft(
        db,
        user_id=user_id,
        filename=payload.filename,
        content_type=payload.content_type,
        sighting_id=payload.sighting_id,
    )
    upload_url, blob_path, expires_at = media_service.generate_sas_url(
        media.id, payload.filename
    )
    return MediaPresignResponse(
        media_id=media.id,
        upload_url=upload_url,
        blob_path=blob_path,
        expires_at=expires_at,
    )


@router.post("/{media_id}/confirm", response_model=MediaRead)
async def confirm_upload(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await media_service.confirm_upload(db, media_id=media_id, user_id=user_id)


@router.get("/{media_id}", response_model=MediaRead)
async def get_media(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await media_service.get_media(db, media_id=media_id, user_id=user_id)
