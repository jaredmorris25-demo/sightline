import logging

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient

from app.config import settings

logger = logging.getLogger(__name__)

_MISSING_CONFIG_WARNING = (
    "Azure AI Search not configured — AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_API_KEY missing"
)


def get_search_client(index_name: str) -> SearchClient | None:
    if not settings.azure_search_endpoint or not settings.azure_search_api_key:
        logger.warning(_MISSING_CONFIG_WARNING)
        return None
    return SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(settings.azure_search_api_key),
    )


def get_index_client() -> SearchIndexClient | None:
    if not settings.azure_search_endpoint or not settings.azure_search_api_key:
        logger.warning(_MISSING_CONFIG_WARNING)
        return None
    return SearchIndexClient(
        endpoint=settings.azure_search_endpoint,
        credential=AzureKeyCredential(settings.azure_search_api_key),
    )
