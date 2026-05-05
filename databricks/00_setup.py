# Databricks notebook source
# MAGIC %md
# MAGIC # Sightline — Environment Setup
# MAGIC Run this notebook once before running any other Sightline notebooks.
# MAGIC Creates the Hive database, tests PostgreSQL connectivity, and verifies GBIF access.

# COMMAND ----------

import psycopg2
import requests

# COMMAND ----------
# MAGIC %md ## 0. Parameters

dbutils.widgets.text("postgres_password", "", "PostgreSQL Password")
postgres_password = dbutils.widgets.get("postgres_password")

if not postgres_password:
    raise ValueError("postgres_password widget is required — enter the DB password before running")

# COMMAND ----------
# MAGIC %md ## 1. Create Hive database

spark.sql("CREATE DATABASE IF NOT EXISTS hive_metastore.sightline")
spark.sql("USE hive_metastore.sightline")

print("SUCCESS  database 'hive_metastore.sightline' ready")

# COMMAND ----------
# MAGIC %md ## 2. Test PostgreSQL connectivity

_pg_dsn = (
    "host=psql-sightline-dev.postgres.database.azure.com "
    "port=5432 "
    "dbname=sightline "
    "user=sightline_admin "
    f"password={postgres_password} "
    "sslmode=require"
)

try:
    with psycopg2.connect(_pg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sightings")
            (sightings_count,) = cur.fetchone()
    print(f"SUCCESS  PostgreSQL connected — {sightings_count:,} sightings in DB")
except psycopg2.OperationalError as exc:
    print(f"FAILURE  PostgreSQL connection failed: {exc}")
    raise

# COMMAND ----------
# MAGIC %md ## 3. Test GBIF API connectivity

try:
    resp = requests.get(
        "https://api.gbif.org/v1/occurrence/search",
        params={"country": "AU", "limit": 1},
        timeout=10,
    )
    resp.raise_for_status()
    total = resp.json().get("count", "unknown")
    print(f"SUCCESS  GBIF API reachable — {total:,} Australian occurrences available")
except requests.RequestException as exc:
    print(f"FAILURE  GBIF API unreachable: {exc}")
    raise

# COMMAND ----------
# MAGIC %md ## 4. Summary

print("=" * 50)
print("Sightline Databricks environment ready")
print("  Database : hive_metastore.sightline")
print(f"  Postgres : psql-sightline-dev.postgres.database.azure.com ({sightings_count:,} sightings)")
print("  GBIF     : https://api.gbif.org/v1")
print("=" * 50)
