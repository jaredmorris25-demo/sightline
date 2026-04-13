# Sightline — Development Log

Reverse-chronological. Add an entry at the end of every session.
Format: `## YYYY-MM-DD — Summary`

---

## 2026-04-13 — Phase 2 complete — GitHub Actions CI green

### Completed
- GitHub Actions CI fully passing: lint (ruff) and test (pytest) jobs both green
- Phase 2 all items complete — SQLAlchemy models, Alembic migration, Pydantic
  schemas, species and sightings endpoints, species seed script, CI pipeline

### Bugs caught and fixed
- ruff: 6 unused imports removed across api/app/models/location.py,
  api/app/models/user.py, api/app/schemas/user.py, api/tests/conftest.py,
  api/tests/test_health.py
- pytest exit code 4 (no tests collected in CI): added api/pytest.ini with
  asyncio_mode = auto and testpaths = tests
- ModuleNotFoundError: No module named 'app' in CI runner: added PYTHONPATH: .
  to the Run pytest step in .github/workflows/api-ci.yml

---

## 2026-04-12 — Species seed script — 255 Australian species from ALA

### Completed
- db/seed/seed_species.py: fetches Australian species from ALA API across 6
  groups, 255 records seeded:
  - Birds: 50
  - Mammals: 50
  - Reptiles: 50
  - Amphibians: 50
  - Fungi: 50
  - Vascular plants: 5 (45 records skipped — missing scientificName in ALA
    response, upstream data quality issue, not a script bug)
- Idempotent via INSERT ... ON CONFLICT (scientific_name) DO NOTHING — confirmed
  working: re-run skips all 250 existing records cleanly, inserts only new ones
- class/order columns confirmed populated in DB after field mapping fix

### Bugs caught and fixed
- Initial mapping used record.get('classs') — corrected to record.get('class')
- ALA group name 'Plants' returns 0 results — fixed to 'Vascular plants'
  (confirmed via API probe: totalRecords=165)

---

## 2026-04-12 — Species and sightings endpoints, tests, spatial query

### Completed
- Species endpoints: GET /v1/species/, GET /v1/species/search, GET /v1/species/{id},
  POST /v1/species/ — all wired via species_service.py
- Sightings endpoints: GET /v1/sightings/, GET /v1/sightings/nearby,
  GET /v1/sightings/{id}, POST /v1/sightings/ — wired via sighting_service.py
- Spatial query: ST_DWithin with geography cast for accurate metre-based radius,
  ordered by ST_Distance. PostGIS longitude-first argument order enforced in comments.
- Transactional rollback test fixture in api/tests/conftest.py — each test runs
  inside a transaction that rolls back on teardown, no data written to DB
- 3 species tests passing (list, search, create)
- Pydantic class-based Config replaced with SettingsConfigDict — deprecation
  warning eliminated

### Bugs caught and fixed
- Missing func. wrapper on ST_MakePoint in get_nearby_sightings
- Missing func. wrapper on ST_DWithin in get_nearby_sightings
- Pydantic v2 class-based config deprecation in api/app/config.py

---

## 2026-04-12 — Pydantic schemas for all 8 entities

### Completed
- Pydantic schemas created for all 8 entities: User, Species, Group,
  GroupMembership, Location, Sighting, Media, IngestRecord
- PaginatedResponse[T] generic envelope in schemas/common.py — used by all
  list endpoints

### Notable decisions
- DwC aliasing on Species: class_name/order_name use alias="class"/"order" with
  populate_by_name=True so JSON API uses correct Darwin Core field names while
  Python avoids reserved keywords
- UserPublic vs UserRead split: UserRead includes email (auth'd self-view only);
  UserPublic strips it for safe embedding in sighting and group responses
- SightingDetail vs SightingRead: list endpoints return SightingRead (flat);
  detail endpoint returns SightingDetail with embedded SpeciesSummary and
  UserPublic to avoid N+1 pressure on list queries
- blob_url excluded from MediaRead — only cdn_url exposed; internal Azure Blob
  Storage URLs stay server-side
- SightingCreate.observed_at validator: rejects naive datetimes explicitly,
  compares against datetime.now(timezone.utc) — no dependence on server timezone
  or client-supplied tzinfo

---

## 2026-04-07 — SQLAlchemy models and initial Alembic migration

### Completed
- 8 SQLAlchemy models created: User, Group, GroupMembership, Species, Sighting,
  Location, Media, IngestRecord — all Darwin Core aligned, PostGIS geometry columns
  with GIST indexes, UUID primary keys, timezone-aware timestamps
- geoalchemy2 added to requirements.txt and Docker image rebuilt
- Alembic fully configured: env.py with sys.path dual-layout (host + container),
  include_object filter to exclude PostGIS/Tiger system tables from autogenerate,
  script.py.mako with geoalchemy2 import
- db/ directory volume-mounted into API container (docker-compose.yml updated)
- Initial migration generated and applied: `alembic upgrade head` clean —
  revision 5d17857927af, all 8 tables present in public schema
- docker-compose.yml: removed obsolete `version: "3.9"` attribute

### Issues encountered and resolved
- PostGIS Tiger geocoder tables (tiger.*, topology.*) detected by autogenerate
  as "removed" tables — fixed by stripping drop statements from migration and
  adding include_object filter to env.py
- GroupType enum stored 'cls' instead of 'class' — fixed via values_callable
  on the SQLAlchemy Enum column and corrected in the migration file
- Alembic container working directory needed DATABASE_URL_SYNC passed inline
  (fallback URL in alembic.ini used localhost, not postgres hostname)

### Deferred
- Pydantic schemas
- Species and sightings API endpoints (Phase 2 continuation)

---

## 2026-04-07 — Phase 1 complete

### Completed
- GitHub repo created at github.com/jaredmorris25-demo/sightline
- Full folder scaffold committed (39 files) — see repo structure in CLAUDE.md
- Docker Compose running locally: PostgreSQL 16/PostGIS, pgAdmin, FastAPI
- FastAPI skeleton with /health and /ready endpoints verified at localhost:8000
- Terraform bootstrapped — remote state backend in Azure (stsightlinetfstate, 
  rg-sightline, australiaeast)
- CLAUDE.md v2 committed — includes phases, schema, design principles

### Decisions made
- Monorepo confirmed (ADR-002)
- Offline capture timestamps as source of truth confirmed (ADR-003)
- Schema fully designed — 8 entities, Darwin Core aligned
- Group/multi-tenancy confirmed as foundational (not additive)

### Issues encountered and resolved
- Git initialised in home directory instead of project folder — resolved by 
  reinitialising git inside ~/sightline/ and force pushing
- Terraform version mismatch (1.5.7 vs required 1.6) — resolved by reinstalling 
  from HashiCorp tap (now 1.14.8)

### Deferred
- Auth0 vs Azure AD B2C decision (Open Question — resolve in Phase 2)
- Species seed strategy not yet decided

### Next session
Phase 2: SQLAlchemy models for all 8 entities, first Alembic migration,
Pydantic schemas, species and sightings endpoints