# Sightline — Azure AI Search backfill script
# Reads all species from the database and upserts them into the Azure AI Search
# species index in batches of 100.
#
# Idempotent: upload_documents uses merge-or-upload semantics.
# Safe to re-run — existing documents are overwritten with current DB values.
#
# Run from repo root:
# docker compose exec \
#   -e DATABASE_URL_SYNC=postgresql://sightline:localdevonly@postgres:5432/sightline \
#   -e AZURE_SEARCH_ENDPOINT=https://search-sightline-dev.search.windows.net \
#   -e AZURE_SEARCH_API_KEY=<key> \
#   api python /db/seed/backfill_search_index.py

import logging
import os
import sys
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
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
# ---------------------------------------------------------------------------
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)

DATABASE_URL_SYNC = os.environ.get("DATABASE_URL_SYNC")
AZURE_SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.environ.get("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX_SPECIES = os.environ.get("AZURE_SEARCH_INDEX_SPECIES", "species")

missing = [k for k, v in {
    "DATABASE_URL_SYNC": DATABASE_URL_SYNC,
    "AZURE_SEARCH_ENDPOINT": AZURE_SEARCH_ENDPOINT,
    "AZURE_SEARCH_API_KEY": AZURE_SEARCH_API_KEY,
}.items() if not v]
if missing:
    log.error("Missing required environment variables: %s", ", ".join(missing))
    sys.exit(1)

BATCH_SIZE = 100

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    engine = create_engine(DATABASE_URL_SYNC)
    client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX_SPECIES,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, common_name, scientific_name, kingdom, family,
                       conservation_status, description
                FROM species
                ORDER BY scientific_name
            """)
        ).fetchall()

    total = len(rows)
    log.info("Fetched %d species from database", total)

    indexed = 0
    for batch_start in range(0, total, BATCH_SIZE):
        batch = rows[batch_start: batch_start + BATCH_SIZE]
        documents = [
            {
                "id": str(row.id),
                "common_name": row.common_name,
                "scientific_name": row.scientific_name,
                "kingdom": row.kingdom,
                "family": row.family,
                "conservation_status": row.conservation_status,
                "description": row.description,
            }
            for row in batch
        ]
        result = client.upload_documents(documents)
        succeeded = sum(1 for r in result if r.succeeded)
        failed = len(result) - succeeded
        indexed += succeeded
        log.info(
            "Batch %d–%d: %d succeeded, %d failed",
            batch_start + 1,
            batch_start + len(batch),
            succeeded,
            failed,
        )
        if failed:
            for r in result:
                if not r.succeeded:
                    log.warning("  Failed key=%s status=%s error=%s", r.key, r.status_code, r.error_message)

    log.info("Backfill complete — %d/%d species indexed", indexed, total)


if __name__ == "__main__":
    main()
