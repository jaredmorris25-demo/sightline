# Sightline — Synthetic sightings seed script
# Generates 10 000 realistic synthetic sightings across Australia for
# development and testing purposes.
#
# Idempotent: checks ingest_records for source_system='synthetic_seed'.
# If count >= 10 000, exits without inserting.
#
# Run against local database:
# docker compose exec -e DATABASE_URL_SYNC=postgresql://sightline:localdevonly@postgres:5432/sightline api python /db/seed/seed_sightings.py
#
# Run against Azure database:
# docker compose exec -e DATABASE_URL_SYNC="postgresql://sightline_admin:PASSWORD@psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require" api python /db/seed/seed_sightings.py

import json
import logging
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
# Environment
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
# Constants
# ---------------------------------------------------------------------------
TARGET_COUNT = 10_000
BATCH_SIZE = 100
LOG_EVERY = 500

# Weighted Australian coordinate regions: (lat_min, lat_max, lng_min, lng_max, weight)
REGIONS = [
    (-38, -27, 150, 154, 0.35),  # Southeast coast (Sydney/Melbourne/Brisbane)
    (-34, -31, 115, 117, 0.15),  # Southwest (Perth)
    (-36, -34, 138, 141, 0.10),  # Adelaide
    (-27, -16, 145, 149, 0.15),  # Queensland coast
    (-14, -12, 130, 132, 0.05),  # NT/Darwin
    (-43, -41, 145, 148, 0.05),  # Tasmania
    (-35, -20, 130, 145, 0.15),  # Inland/outback (sparse)
]
REGION_WEIGHTS = [r[4] for r in REGIONS]

BEHAVIOUR_OPTIONS = [
    "Foraging", "Perched", "In flight", "Calling", "Nesting",
    "Drinking", "Roosting", "Swimming", "Hunting", "Resting", "Displaying",
]

NOW = datetime.now(timezone.utc)
TWO_YEARS_AGO = NOW - timedelta(days=730)
TOTAL_SECONDS = int((NOW - TWO_YEARS_AGO).total_seconds())

# ---------------------------------------------------------------------------
# Generator functions
# ---------------------------------------------------------------------------

def generate_coordinates() -> tuple[float, float]:
    region = random.choices(REGIONS, weights=REGION_WEIGHTS, k=1)[0]
    lat_min, lat_max, lng_min, lng_max, _ = region
    lat = random.uniform(lat_min, lat_max)
    lng = random.uniform(lng_min, lng_max)
    return lat, lng


def generate_observed_at() -> datetime:
    offset = timedelta(seconds=random.randint(0, TOTAL_SECONDS))
    dt = TWO_YEARS_AGO + offset

    # 70% of sightings fall during daylight hours (06:00–19:00)
    if random.random() < 0.70:
        dt = dt.replace(hour=random.randint(6, 19), minute=random.randint(0, 59))

    # Weekend skew — 20% chance of shifting a weekday observation to Saturday
    if dt.weekday() < 5 and random.random() < 0.20:
        candidate = dt + timedelta(days=(5 - dt.weekday()))
        if candidate <= NOW:
            dt = candidate

    return dt


def generate_count() -> int:
    roll = random.random()
    if roll < 0.70:
        return 1
    elif roll < 0.90:
        return random.randint(2, 5)
    else:
        return random.randint(6, 20)


def generate_visibility() -> str:
    roll = random.random()
    if roll < 0.80:
        return "public"
    elif roll < 0.95:
        return "group"
    else:
        return "private"


def generate_behaviour() -> str | None:
    if random.random() < 0.40:
        return None
    return random.choice(BEHAVIOUR_OPTIONS)


# ---------------------------------------------------------------------------
# SQL templates
# ---------------------------------------------------------------------------

INSERT_SIGHTING = text("""
    INSERT INTO sightings (
        id, user_id, species_id, observed_at, geometry,
        count, behaviour_notes, visibility, verified
    )
    VALUES (
        :id,
        :user_id,
        :species_id,
        :observed_at,
        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
        :count,
        :behaviour_notes,
        CAST(:visibility AS visibility),
        false
    )
""")

INSERT_INGEST = text("""
    INSERT INTO ingest_records (
        id, source_format, source_system, source_reference,
        raw_payload, submitted_by, mapping_confidence, canonical_sighting_id
    )
    VALUES (
        :id,
        CAST('api' AS sourceformat),
        'synthetic_seed',
        'development_data',
        CAST(:raw_payload AS jsonb),
        :submitted_by,
        1.0,
        :canonical_sighting_id
    )
""")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    engine = create_engine(DATABASE_URL_SYNC)

    with engine.begin() as conn:

        # --- Idempotency check -------------------------------------------
        existing = conn.execute(
            text(
                "SELECT COUNT(*) FROM ingest_records "
                "WHERE source_system = 'synthetic_seed'"
            )
        ).scalar()
        if existing >= TARGET_COUNT:
            log.info(
                "Synthetic sightings already seeded (%d records found). Exiting.",
                existing,
            )
            return

        # --- User lookup --------------------------------------------------
        user_row = conn.execute(
            text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")
        ).fetchone()
        if not user_row:
            log.error(
                "No users found — log in to the web app first to "
                "auto-provision your user account."
            )
            sys.exit(1)
        user_id = str(user_row[0])
        log.info("Using user_id: %s", user_id)

        # --- Species lookup -----------------------------------------------
        species_rows = conn.execute(text("SELECT id FROM species")).fetchall()
        if not species_rows:
            log.error("No species found — run seed_species.py first.")
            sys.exit(1)
        species_ids = [str(row[0]) for row in species_rows]
        log.info("Loaded %d species.", len(species_ids))

        # --- Batch insert loop --------------------------------------------
        total_inserted = 0
        sighting_batch: list[dict] = []
        ingest_batch: list[dict] = []

        for i in range(TARGET_COUNT):
            sighting_id = str(uuid.uuid4())
            lat, lng = generate_coordinates()
            observed_at = generate_observed_at()
            species_id = random.choice(species_ids)

            sighting_batch.append({
                "id": sighting_id,
                "user_id": user_id,
                "species_id": species_id,
                "observed_at": observed_at,
                "lat": lat,
                "lng": lng,
                "count": generate_count(),
                "behaviour_notes": generate_behaviour(),
                "visibility": generate_visibility(),
            })

            ingest_batch.append({
                "id": str(uuid.uuid4()),
                "submitted_by": user_id,
                "raw_payload": json.dumps({
                    "lat": lat,
                    "lng": lng,
                    "species_id": species_id,
                    "observed_at": observed_at.isoformat(),
                }),
                "canonical_sighting_id": sighting_id,
            })

            if len(sighting_batch) == BATCH_SIZE:
                conn.execute(INSERT_SIGHTING, sighting_batch)
                conn.execute(INSERT_INGEST, ingest_batch)
                total_inserted += len(sighting_batch)
                sighting_batch = []
                ingest_batch = []

                if total_inserted % LOG_EVERY == 0:
                    log.info("Inserted %d / %d sightings...", total_inserted, TARGET_COUNT)

        # Flush any remaining records in a partial final batch
        if sighting_batch:
            conn.execute(INSERT_SIGHTING, sighting_batch)
            conn.execute(INSERT_INGEST, ingest_batch)
            total_inserted += len(sighting_batch)

    log.info("Seed complete — %d synthetic sightings inserted.", total_inserted)


if __name__ == "__main__":
    main()
