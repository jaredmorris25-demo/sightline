# Sightline Databricks Configuration
# All secrets loaded from Databricks secrets or widgets — never hardcoded

POSTGRES_HOST = "psql-sightline-dev.postgres.database.azure.com"
POSTGRES_PORT = 5432
POSTGRES_DB = "sightline"
POSTGRES_USER = "sightline_admin"
# POSTGRES_PASSWORD — loaded from Databricks secret scope

GBIF_BASE_URL = "https://api.gbif.org/v1"
GBIF_DATASET_AUSTRALIA = "dr2699"  # ALA Australia dataset key

DELTA_CATALOG = "dbw_weather_jm1535"
DELTA_DATABASE = "sightline"
DELTA_SCHEMA = "sightline"
JDBC_URL = "jdbc:postgresql://psql-sightline-dev.postgres.database.azure.com:5432/sightline?sslmode=require"

TABLE_RAW_GBIF = "raw_gbif_occurrences"
TABLE_CANONICAL = "canonical_sightings"
TABLE_HEATMAP = "heatmap_grid"
TABLE_TIMESERIES = "timeseries_monthly"
TABLE_SPECIES_SUMMARY = "species_summary"
