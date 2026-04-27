import asyncio
import logging

from azure.search.documents.indexes.models import (
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
)

from app.config import settings
from app.search.client import get_index_client, get_search_client

logger = logging.getLogger(__name__)


def _species_index() -> SearchIndex:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="common_name", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="scientific_name", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="kingdom", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="family", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="conservation_status", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="description", type=SearchFieldDataType.String),
    ]
    return SearchIndex(name=settings.azure_search_index_species, fields=fields)


def _sightings_index() -> SearchIndex:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="species_common_name", type=SearchFieldDataType.String),
        SearchableField(name="species_scientific_name", type=SearchFieldDataType.String),
        SearchableField(name="behaviour_notes", type=SearchFieldDataType.String),
        SearchableField(name="location_description", type=SearchFieldDataType.String),
        SimpleField(
            name="observed_at",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
            sortable=True,
        ),
        SimpleField(name="latitude", type=SearchFieldDataType.Double, filterable=True),
        SimpleField(name="longitude", type=SearchFieldDataType.Double, filterable=True),
        SimpleField(name="visibility", type=SearchFieldDataType.String, filterable=True),
    ]
    return SearchIndex(name=settings.azure_search_index_sightings, fields=fields)


async def create_indexes() -> None:
    logger.info("create_indexes() called")
    idx_client = get_index_client()
    if idx_client is None:
        logger.warning("create_indexes() skipped — no index client (credentials missing)")
        return

    def _create():
        for index in [_species_index(), _sightings_index()]:
            logger.info("Creating/updating index: %s", index.name)
            try:
                idx_client.create_or_update_index(index)
                logger.info("Search index ready: %s", index.name)
            except Exception:
                logger.warning("Failed to create index: %s", index.name, exc_info=True)

    await asyncio.to_thread(_create)
    logger.info("create_indexes() complete")


async def index_species(species) -> None:
    client = get_search_client(settings.azure_search_index_species)
    if client is None:
        return
    doc = {
        "id": str(species.id),
        "common_name": species.common_name,
        "scientific_name": species.scientific_name,
        "kingdom": species.kingdom,
        "family": species.family,
        "conservation_status": species.conservation_status,
        "description": species.description,
    }
    await asyncio.to_thread(client.upload_documents, [doc])
    logger.debug("Indexed species %s", species.id)


async def index_sighting(sighting, species, latitude: float | None, longitude: float | None) -> None:
    client = get_search_client(settings.azure_search_index_sightings)
    if client is None:
        return
    doc = {
        "id": str(sighting.id),
        "species_common_name": species.common_name if species else None,
        "species_scientific_name": species.scientific_name if species else None,
        "behaviour_notes": sighting.behaviour_notes,
        "location_description": sighting.location_description,
        "observed_at": sighting.observed_at.isoformat() if sighting.observed_at else None,
        "latitude": latitude,
        "longitude": longitude,
        "visibility": sighting.visibility.value if sighting.visibility else None,
    }
    await asyncio.to_thread(client.upload_documents, [doc])
    logger.debug("Indexed sighting %s", sighting.id)
