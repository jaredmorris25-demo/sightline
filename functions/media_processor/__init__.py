import logging
import os
from urllib.parse import urlparse

import azure.functions as func
from azure.storage.blob import BlobServiceClient

from . import db_updater, exif_handler, image_processor

LOG = logging.getLogger(__name__)


def main(event: func.EventGridEvent) -> None:
    LOG.info("[media_processor] triggered event_id=%s", event.id)

    data = event.get_json()
    blob_url = data["url"]
    LOG.info("[media_processor] blob_url=%s", blob_url)

    # Parse container and blob path from URL.
    # Format: https://{account}.blob.core.windows.net/{container}/{media_id}/{filename}
    parsed = urlparse(blob_url)
    path_parts = parsed.path.lstrip("/").split("/", 1)
    container_name = path_parts[0]
    blob_path = path_parts[1]  # {media_id}/{filename}
    LOG.info("[media_processor] container=%s blob_path=%s", container_name, blob_path)

    # media_id is the first path segment before the filename.
    media_id = blob_path.split("/")[0]

    connection_string = os.environ["MEDIA_STORAGE_CONNECTION"]
    blob_service = BlobServiceClient.from_connection_string(connection_string)

    LOG.info("[media_processor] downloading blob")
    blob_client = blob_service.get_blob_client(container=container_name, blob=blob_path)
    image_bytes = blob_client.download_blob().readall()

    LOG.info("[media_processor] extracting EXIF")
    exif_result = exif_handler.extract_exif(image_bytes)

    LOG.info("[media_processor] generating thumbnail")
    thumbnail_bytes = image_processor.generate_thumbnail(image_bytes)

    LOG.info("[media_processor] stripping GPS")
    image_processor.strip_gps(image_bytes)

    processed_container = os.environ["MEDIA_CONTAINER_PROCESSED"]
    thumb_blob_path = _thumb_name(blob_path)

    LOG.info("[media_processor] uploading thumbnail blob_path=%s", thumb_blob_path)
    thumb_client = blob_service.get_blob_client(
        container=processed_container, blob=thumb_blob_path
    )
    thumb_client.upload_blob(thumbnail_bytes, overwrite=True)

    cdn_host = os.environ["CDN_ENDPOINT"]
    cdn_url = f"https://{cdn_host}/{thumb_blob_path}"

    LOG.info("[media_processor] updating database media_id=%s", media_id)
    db_updater.update_media_record(
        media_id=media_id,
        cdn_url=cdn_url,
        exif_data=exif_result.get("raw_exif"),
        observed_at_device=exif_result.get("observed_at_device"),
        gps_lat=exif_result.get("gps_lat"),
        gps_lng=exif_result.get("gps_lng"),
    )

    LOG.info("[media_processor] complete media_id=%s", media_id)


def _thumb_name(blob_path: str) -> str:
    """foo/bar.jpg → foo/bar-thumb.jpg"""
    filename = blob_path.rsplit("/", 1)[-1]
    if "." in filename:
        base, ext = blob_path.rsplit(".", 1)
        return f"{base}-thumb.{ext}"
    return f"{blob_path}-thumb"
