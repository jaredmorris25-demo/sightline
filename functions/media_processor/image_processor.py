import io
import logging

from PIL import Image

LOG = logging.getLogger(__name__)

_GPS_IFD_TAG = 34853


def generate_thumbnail(image_bytes: bytes, max_size: int = 400) -> bytes:
    """
    Resize to max_size on the longest dimension (aspect ratio preserved).
    Converts to RGB to handle PNG transparency before saving as JPEG.
    """
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()


def strip_gps(image_bytes: bytes) -> bytes:
    """
    Remove the GPSInfo IFD from EXIF and return re-encoded image bytes.
    Returns original bytes unchanged if no GPS data is present.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        exif = img.getexif()
        if _GPS_IFD_TAG not in exif:
            return image_bytes
        del exif[_GPS_IFD_TAG]
        output = io.BytesIO()
        img.save(output, format=img.format or "JPEG", exif=exif.tobytes())
        return output.getvalue()
    except Exception as exc:
        LOG.warning("[image_processor] GPS strip failed, returning original: %s", exc)
        return image_bytes
