import json
import logging
import os
from datetime import datetime

from sqlalchemy import create_engine, text

LOG = logging.getLogger(__name__)


def update_media_record(
    media_id: str,
    cdn_url: str | None,
    exif_data: dict | None,
    observed_at_device: datetime | None,
    gps_lat: float | None,
    gps_lng: float | None,
) -> None:
    # DATABASE_URL may be the asyncpg variant used by FastAPI — strip the driver
    # suffix and convert asyncpg ssl param to psycopg2 sslmode param.
    database_url = (
        os.environ["DATABASE_URL"]
        .replace("+asyncpg", "")
        .replace("?ssl=require", "?sslmode=require")
    )
    engine = create_engine(database_url)

    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE media SET
                        status             = 'ready',
                        cdn_url            = :cdn_url,
                        exif_data          = CAST(:exif_data AS jsonb),
                        observed_at_device = COALESCE(observed_at_device, :observed_at_device),
                        exif_lat           = :exif_lat,
                        exif_lng           = :exif_lng,
                        gps_stripped       = true,
                        synced_at          = NOW()
                    WHERE id = :media_id
                """),
                {
                    "media_id": media_id,
                    "cdn_url": cdn_url,
                    "exif_data": json.dumps(exif_data) if exif_data else None,
                    "observed_at_device": observed_at_device,
                    "exif_lat": gps_lat,
                    "exif_lng": gps_lng,
                },
            )
        LOG.info("[db_updater] updated media_id=%s", media_id)
    except Exception as exc:
        LOG.error("[db_updater] failed to update media_id=%s: %s", media_id, exc)
        raise
    finally:
        engine.dispose()
