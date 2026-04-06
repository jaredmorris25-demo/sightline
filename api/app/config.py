from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://sightline:sightline@localhost:5432/sightline"
    database_url_sync: str = "postgresql://sightline:sightline@localhost:5432/sightline"

    # Auth0
    auth0_domain: str = ""
    auth0_api_audience: str = ""
    auth0_client_id: str = ""
    auth0_client_secret: str = ""

    # Azure Storage
    azure_storage_account_name: str = ""
    azure_storage_container_sightings: str = "sightings-media"
    azure_storage_container_ingest: str = "ingest-raw"
    azure_cdn_endpoint: str = ""

    # Azure Service Bus
    azure_servicebus_connection_string: str = ""
    azure_servicebus_queue_media: str = "media-processing"

    # Azure AI Search
    azure_search_endpoint: str = ""
    azure_search_api_key: str = ""
    azure_search_index_species: str = "species"
    azure_search_index_sightings: str = "sightings"

    # App
    environment: str = "local"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
