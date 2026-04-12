# Sightline — Species seed script
# Fetches Australian species from the Atlas of Living Australia (ALA) API
# and inserts them into the local PostgreSQL database.
#
# Idempotent: uses INSERT ... ON CONFLICT (scientific_name) DO NOTHING.
# Safe to run multiple times with identical results.
#
# Run from repo root:
# docker compose exec -e DATABASE_URL_SYNC=postgresql://sightline:localdevonly@postgres:5432/sightline api python /db/seed/seed_species.py

import logging
import os
import sys
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment — load .env relative to repo root (../../ from db/seed/)
# Falls back gracefully if DATABASE_URL_SYNC is already set in the environment.
# ---------------------------------------------------------------------------
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)

DATABASE_URL_SYNC = os.environ.get("DATABASE_URL_SYNC")
if not DATABASE_URL_SYNC:
    log.error(
        "DATABASE_URL_SYNC is not set. "
        "Pass it via the docker compose exec -e flag or .env file."
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# ALA API configuration
# ---------------------------------------------------------------------------
ALA_SEARCH_URL = "https://api.ala.org.au/species/search"
ALA_GROUPS = ["Birds", "Mammals", "Reptiles", "Amphibians", "Vascular plants", "Fungi"]
ALA_PAGE_SIZE = 50

# ---------------------------------------------------------------------------
# ALA record → Species row mapping
# ---------------------------------------------------------------------------

def map_ala_record(record: dict) -> dict | None:
    """
    Map a single ALA search result record to a Species table row dict.

    Returns None if the record has no scientificName (row will be skipped).

    ALA field notes:
    - commonNameSingle is preferred over commonName (which may be a list string).
    - guid is ALA's stable taxon identifier, mapped to ala_id.
    - conservationStatus is absent on most records; mapped when present.
    """
    scientific_name = (record.get("scientificName") or "").strip()
    if not scientific_name:
        return None

    return {
        "id": str(uuid.uuid4()),
        "scientific_name": scientific_name,
        "common_name": (
            record.get("commonNameSingle")
            or record.get("commonName")
            or None
        ),
        "kingdom": record.get("kingdom") or None,
        "phylum": record.get("phylum") or None,
        "class_name": record.get("class") or None,
        "order_name": record.get("order") or None,
        "family": record.get("family") or None,
        "genus": record.get("genus") or None,
        "ala_id": record.get("guid") or None,
        "conservation_status": record.get("conservationStatus") or None,
    }


# ---------------------------------------------------------------------------
# Upsert logic
# ---------------------------------------------------------------------------

def upsert_species(conn, rows: list[dict]) -> tuple[int, int]:
    """
    Insert species rows using ON CONFLICT (scientific_name) DO NOTHING.

    Returns (inserted, skipped) counts.
    Before insert, query the current count so we can calculate actual inserts
    from rowcount (which is unreliable for DO NOTHING in some drivers).
    """
    if not rows:
        return 0, 0

    # Count existing matching scientific names so we can compute skips.
    names = [r["scientific_name"] for r in rows]
    existing_count = conn.execute(
        text(
            "SELECT COUNT(*) FROM species WHERE scientific_name = ANY(:names)"
        ),
        {"names": names},
    ).scalar()

    conn.execute(
        text("""
            INSERT INTO species (
                id, scientific_name, common_name,
                kingdom, phylum, class, "order",
                family, genus, ala_id, conservation_status
            )
            VALUES (
                :id, :scientific_name, :common_name,
                :kingdom, :phylum, :class_name, :order_name,
                :family, :genus, :ala_id, :conservation_status
            )
            ON CONFLICT (scientific_name) DO NOTHING
        """),
        rows,
    )

    inserted = len(rows) - existing_count
    skipped = existing_count
    return inserted, skipped


# ---------------------------------------------------------------------------
# Fetch from ALA
# ---------------------------------------------------------------------------

def fetch_ala_group(group: str) -> list[dict]:
    """
    Fetch one page of species for the given ALA species group.

    Returns a list of raw ALA record dicts, or [] on non-200 response.
    """
    params = {
        "q": "*",
        "fq": [f"rank:species", f"speciesGroup:{group}"],
        "pageSize": ALA_PAGE_SIZE,
    }
    try:
        response = requests.get(ALA_SEARCH_URL, params=params, timeout=15)
    except requests.RequestException as exc:
        log.warning("Network error fetching group '%s': %s", group, exc)
        return []

    if response.status_code != 200:
        log.warning(
            "ALA API returned %s for group '%s' — skipping.",
            response.status_code,
            group,
        )
        return []

    data = response.json()
    results = data.get("searchResults", {}).get("results", [])
    log.info("Fetched %d records from ALA for group '%s'.", len(results), group)
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    engine = create_engine(DATABASE_URL_SYNC)
    total_inserted = 0
    total_skipped = 0
    total_invalid = 0

    with engine.begin() as conn:
        for group in ALA_GROUPS:
            records = fetch_ala_group(group)
            if not records:
                continue

            rows = []
            invalid = 0
            for record in records:
                row = map_ala_record(record)
                if row is None:
                    invalid += 1
                    continue
                rows.append(row)

            if invalid:
                log.warning(
                    "Group '%s': skipped %d record(s) with no scientificName.",
                    group,
                    invalid,
                )

            inserted, skipped = upsert_species(conn, rows)
            log.info(
                "Group '%s': %d inserted, %d skipped (duplicates), %d invalid.",
                group,
                inserted,
                skipped,
                invalid,
            )
            total_inserted += inserted
            total_skipped += skipped
            total_invalid += invalid

    log.info(
        "Seed complete — total inserted: %d, duplicates skipped: %d, invalid: %d.",
        total_inserted,
        total_skipped,
        total_invalid,
    )


if __name__ == "__main__":
    main()
