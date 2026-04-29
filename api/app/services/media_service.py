import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient as AsyncBlobServiceClient
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.media import Media, MediaStatus, MediaType

_CONTENT_TYPE_TO_MEDIA_TYPE: dict[str, MediaType] = {
    "image/jpeg": MediaType.photo,
    "image/png": MediaType.photo,
    "image/heic": MediaType.photo,
    "video/mp4": MediaType.video,
}


async def create_media_draft(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    filename: str,
    content_type: str,
    sighting_id: uuid.UUID | None,
) -> Media:
    media_type = _CONTENT_TYPE_TO_MEDIA_TYPE[content_type]

    # UUID is Python-generated — available immediately, no flush required.
    media = Media(
        user_id=user_id,
        sighting_id=sighting_id,
        status=MediaStatus.draft,
        media_type=media_type,
        mime_type=content_type,
    )

    # Store the permanent blob URL (not the SAS URL) so confirm_upload knows
    # exactly which blob to verify without re-deriving the path.
    blob_path = f"{media.id}/{filename}"
    media.blob_url = (
        f"https://{settings.azure_storage_account_name}.blob.core.windows.net"
        f"/{settings.azure_storage_container_raw}/{blob_path}"
    )

    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media


def generate_sas_url(
    media_id: uuid.UUID,
    filename: str,
) -> tuple[str, str, datetime]:
    """
    Generate a write-only SAS URL for direct client upload to Azure Blob Storage.
    Returns (upload_url, blob_path, expires_at).

    The SAS token grants PUT access to a single blob for 15 minutes only.
    The client uses the upload_url directly — the API never proxies the file bytes.
    """
    blob_service = BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )
    account_name = blob_service.account_name
    account_key = blob_service.credential.account_key

    blob_path = f"{media_id}/{filename}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=settings.azure_storage_container_raw,
        blob_name=blob_path,
        account_key=account_key,
        permission=BlobSasPermissions(write=True),
        expiry=expires_at,
    )

    upload_url = (
        f"https://{account_name}.blob.core.windows.net"
        f"/{settings.azure_storage_container_raw}/{blob_path}?{sas_token}"
    )
    return upload_url, blob_path, expires_at


async def confirm_upload(
    db: AsyncSession,
    *,
    media_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Media:
    media = await _get_media_or_404(db, media_id, user_id)

    if media.blob_url is None:
        raise HTTPException(status_code=400, detail="No blob URL on record")

    # Derive blob path from the stored permanent URL.
    # blob_url format: https://{account}.blob.core.windows.net/{container}/{media_id}/{filename}
    parsed = urlparse(media.blob_url)
    blob_path = "/".join(parsed.path.lstrip("/").split("/")[1:])

    async with AsyncBlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    ) as client:
        blob_client = client.get_blob_client(
            container=settings.azure_storage_container_raw,
            blob=blob_path,
        )
        if not await blob_client.exists():
            raise HTTPException(
                status_code=422,
                detail="Upload not found in storage — complete the upload before confirming",
            )

    media.status = MediaStatus.processing
    media.uploaded_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(media)
    return media


async def get_media(
    db: AsyncSession,
    *,
    media_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Media:
    return await _get_media_or_404(db, media_id, user_id)


async def _get_media_or_404(
    db: AsyncSession,
    media_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Media:
    result = await db.execute(
        select(Media).where(Media.id == media_id, Media.user_id == user_id)
    )
    media = result.scalar_one_or_none()
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return media
