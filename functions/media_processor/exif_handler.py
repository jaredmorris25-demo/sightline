import io
import logging
from datetime import datetime, timezone
from typing import Any

from PIL import ExifTags, Image

LOG = logging.getLogger(__name__)

_GPS_IFD_TAG = 34853
_GPS_LATITUDE = 2
_GPS_LATITUDE_REF = 1
_GPS_LONGITUDE = 4
_GPS_LONGITUDE_REF = 3


def extract_exif(image_bytes: bytes) -> dict[str, Any]:
    """
    Returns a dict with keys: raw_exif, observed_at_device, gps_lat, gps_lng.
    Returns an empty dict if no EXIF is present or extraction fails.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        raw = img.getexif()
        if not raw:
            return {}

        exif_dict: dict[str, Any] = {}
        for tag_id, value in raw.items():
            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
            try:
                exif_dict[tag_name] = _to_serialisable(value)
            except Exception:
                pass

        result: dict[str, Any] = {"raw_exif": exif_dict}

        # Prefer DateTimeOriginal (capture time); fall back to DateTime (file time).
        dt_str = exif_dict.get("DateTimeOriginal") or exif_dict.get("DateTime")
        if dt_str:
            parsed_dt = _parse_exif_datetime(str(dt_str))
            if parsed_dt:
                result["observed_at_device"] = parsed_dt

        gps_ifd = raw.get_ifd(_GPS_IFD_TAG)
        if gps_ifd:
            lat = _dms_to_decimal(
                gps_ifd.get(_GPS_LATITUDE),
                str(gps_ifd.get(_GPS_LATITUDE_REF, "N")),
            )
            lng = _dms_to_decimal(
                gps_ifd.get(_GPS_LONGITUDE),
                str(gps_ifd.get(_GPS_LONGITUDE_REF, "E")),
            )
            if lat is not None and lng is not None:
                result["gps_lat"] = lat
                result["gps_lng"] = lng

        return result

    except Exception as exc:
        LOG.warning("[exif_handler] extraction failed: %s", exc)
        return {}


def _parse_exif_datetime(value: str) -> datetime | None:
    try:
        # EXIF format: "2026:04:15 14:32:00" — no timezone embedded.
        # Stored as UTC; true offset unknown without device locale data.
        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


def _dms_to_decimal(dms: Any, ref: str) -> float | None:
    if dms is None:
        return None
    try:
        d, m, s = (float(x) for x in dms)
        decimal = d + m / 60 + s / 3600
        if ref in ("S", "W"):
            decimal = -decimal
        return round(decimal, 7)
    except (TypeError, ValueError):
        return None


def _to_serialisable(value: Any) -> Any:
    """Coerce Pillow EXIF types to JSON-safe Python primitives."""
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, tuple):
        return [_to_serialisable(v) for v in value]
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        # IFDRational — convert to float
        return float(value)
    return value
