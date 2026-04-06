"""
Alembic migration environment.

Adds api/ to sys.path so app.models can be imported, then wires up
Base.metadata for autogenerate. Connection URL is read from the
DATABASE_URL_SYNC environment variable (falls back to alembic.ini value).
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Make api/ importable when running from db/
# Handles two layouts:
#   host  : /path/to/sightline/db/alembic/env.py  → ../../api
#   container: db/ mounted at /db, api/ mounted at /app
# ---------------------------------------------------------------------------
_candidates = [
    Path(__file__).resolve().parents[2] / "api",  # host layout
    Path("/app"),                                   # container layout
]
_api_path = next((str(p) for p in _candidates if (p / "app").is_dir()), None)
if _api_path is None:
    raise RuntimeError("Cannot locate api/ package. Check sys.path candidates in env.py.")
if _api_path not in sys.path:
    sys.path.insert(0, _api_path)

# Import Base and all models — this registers them with Base.metadata.
from app.db.base import Base  # noqa: E402
import app.models  # noqa: F401, E402

# ---------------------------------------------------------------------------
# Alembic config + logging
# ---------------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# PostGIS system table exclusion
# ---------------------------------------------------------------------------
# PostGIS (and the Tiger geocoder extension) ship with tables in the public
# schema that Alembic would otherwise try to drop when autogenerating migrations.
# This filter tells autogenerate to ignore any table that isn't in our own
# models, preventing accidental drops of extension-owned tables.
_POSTGIS_TABLE_PREFIXES = (
    "tiger", "tiger_data", "topology",
)

_POSTGIS_EXACT_TABLES = frozenset({
    # PostGIS core
    "spatial_ref_sys", "layer", "topology",
    # Tiger geocoder lookup tables
    "geocode_settings", "geocode_settings_default",
    "pagc_lex", "pagc_gaz", "pagc_rules",
    "loader_platform", "loader_variables", "loader_lookuptables",
    "street_type_lookup", "direction_lookup", "secondary_unit_lookup",
    "state_lookup", "county_lookup", "countysub_lookup", "place_lookup",
    "zip_lookup", "zip_lookup_base", "zip_lookup_all",
    "zip_state", "zip_state_loc",
    # Tiger geography tables
    "state", "county", "cousub", "place",
    "bg", "tabblock", "tabblock20",
    "tract", "faces", "edges", "addrfeat", "addr", "featnames", "zcta5",
})

_OUR_TABLES = frozenset(Base.metadata.tables.keys())


def include_object(obj, name, type_, reflected, compare_to):
    """Exclude PostGIS extension tables from autogenerate comparisons."""
    if type_ == "table":
        if name in _OUR_TABLES:
            return True
        if name in _POSTGIS_EXACT_TABLES:
            return False
        if any(name.startswith(p) for p in _POSTGIS_TABLE_PREFIXES):
            return False
        # Exclude any reflected table not in our metadata (extension-owned)
        if reflected and name not in _OUR_TABLES:
            return False
    return True


def get_url() -> str:
    return os.environ.get(
        "DATABASE_URL_SYNC",
        config.get_main_option("sqlalchemy.url", ""),
    )


# ---------------------------------------------------------------------------
# Offline mode — generates SQL without a live DB connection
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — requires a live DB connection
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
