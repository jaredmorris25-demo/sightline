# Sightline — Development Log

Reverse-chronological. Add an entry at the end of every session.
Format: `## YYYY-MM-DD — Summary`

---

## 2026-04-24 — Phase 4 CD pipeline complete

### Completed
- `.github/workflows/api-deploy.yml`: three-job CD pipeline on push to develop
  - `test`: PostGIS service container, Alembic migrations, pytest (identical to CI)
  - `build-and-push`: Azure login, ACR login, `docker buildx build --platform linux/amd64`,
    tagged with both `github.sha` (immutable) and `latest`
  - `deploy`: gated on GitHub Actions `dev` environment with required reviewer (manual
    approval); updates Container App with SHA tag; smoke tests `/health` endpoint
- Paths filter covers `api/**`, `api/Dockerfile.prod`, and the workflow file itself
- Branch protection rules configured: main and develop both require PRs
- Workflow file committed on `feature/cd-pipeline`, fix committed on `feature/fix-cd-trigger`

### Key lessons
- Apple Silicon (ARM64) builds push linux/arm64 images by default — Azure Container Apps
  requires linux/amd64; must pass `--platform linux/amd64` to `docker buildx build`
- Terraform state drift: resources created or modified via CLI (`az`) are not reflected
  in state; subsequent `terraform apply` can conflict or recreate resources unexpectedly
- Failed Container App provisioning recovery: delete via `az containerapp delete`, push
  a valid amd64 image to ACR first, then re-run `terraform apply`
- Branch protection on develop means direct pushes are rejected; all changes go through
  feature branches and PRs

### Notes
- ADO migration flagged as future phase consideration — GitHub Actions sufficient for now
- GitHub Actions `dev` environment must be created manually in repo Settings →
  Environments before the approval gate activates

---

## 2026-04-16 — Phase 4 Part A complete — Azure infrastructure live

### Completed
- Terraform modules created: registry, database, keyvault, api
- infra/environments/dev/main.tf wires all modules; backend state in
  Azure Blob Storage (stsightlinetfstate, dev.terraform.tfstate)
- api/Dockerfile.prod: multi-stage linux/amd64 production image,
  uvicorn --workers 2, no --reload
- terraform apply: all 10 resources created in australiaeast / rg-sightline

### Azure resources live
- ACR: acrsightline.azurecr.io
- PostgreSQL Flexible Server: psql-sightline-dev.postgres.database.azure.com
  (PostgreSQL 16, B_Standard_B1ms, 32GB, PostGIS extension enabled)
- Key Vault: kv-sightline-dev.vault.azure.net
- Container Apps Environment: cae-sightline-dev
- Container App: ca-sightline-api (0.5 CPU, 1Gi, min 1 / max 3 replicas)
- Public API URL: https://ca-sightline-api--qk6j3jf.wittywave-8fb8cdba.australiaeast.azurecontainerapps.io
- Alembic migrations applied to Azure PostgreSQL
- 255 Australian species seeded from ALA

### Bugs caught and fixed
- high_availability block does not accept mode="Disabled" in AzureRM 3.x —
  removed block entirely to disable HA
- Image pushed as linux/arm64 (Mac M-series default) — Azure Container Apps
  requires linux/amd64; rebuilt with --platform linux/amd64
- Container App created in Failed state (no image on first apply) — deleted
  via az CLI and recreated after amd64 image was pushed

---

## 2026-04-15 — Phase 3 complete — submit form, nav updates, end-to-end flow confirmed

### Completed
- web/src/app/submit/page.tsx: server component — checks session, redirects
  unauthenticated users to /auth/login, passes accessToken to form
- web/src/app/submit/SubmitSightingForm.tsx: client component — species search
  with 300ms debounce + dropdown, datetime-local (capped at now), lat/lng
  pre-populated from Geolocation API, count, behaviour notes, visibility,
  location description; posts to /v1/sightings/ with Bearer token; redirects
  to / on success, shows inline error on failure
- web/src/app/layout.tsx: "Submit sighting" nav link added, visible only when
  session is active; placed between Species and Logout
- web/src/app/page.tsx: removed duplicate Login/Logout overlay from map —
  auth controls now live only in the nav
- Full end-to-end flow confirmed: form submission → JWT auth → 201 Created →
  redirect to map → sighting appears in GET /v1/sightings/ response

### First real sighting recorded
- Species: Laughing Kookaburra (Dacelo (Dacelo) novaeguineae)
- Location: Brisbane (-27.4698, 153.0251)
- Date: 2026-04-15
- DB id: b1ec161b-9262-4baf-bb80-67cb9ff06319

---

## 2026-04-15 — Full auth flow confirmed end-to-end

### Completed
- Full Auth0 authentication flow working: JWT validated in FastAPI, user
  auto-provisioned in DB on first login, 200 from POST /v1/users/me confirmed
- api/app/routers/users.py: added db.commit() so the flushed User row is
  actually persisted — without this, flush() wrote to the transaction but
  never committed, leaving the users table empty
- api/app/auth/dependencies.py: added logging.warning for JWTError and
  logging.info for audience/issuer to diagnose 401s
- web/src/app/layout.tsx: replaced getAccessToken() (wrong v4 API) with
  session.tokenSet.accessToken — the correct server-side path in Auth0 v4
- web/src/lib/auth0.ts: Auth0Client configured with audience in
  authorizationParameters so access tokens are JWT (not opaque) and carry
  the correct audience claim for FastAPI validation
- Next.js 16 frontend scaffolded: map page, species browser + detail,
  Auth0 proxy.ts, typed API client, QueryClientProvider

### Root causes resolved
- Opaque token: audience not passed in authorizationParameters → Auth0
  issued opaque tokens that FastAPI couldn't validate; fixed in lib/auth0.ts
- flush without commit: get_or_create_user called db.flush() but the users
  router never called db.commit(), so rows were never written to disk

---

## 2026-04-14 — Auth0 JWT middleware and get_or_create_user

### Completed
- api/app/auth/dependencies.py: get_current_user dependency validates RS256
  Bearer tokens against Auth0 JWKS; 24-hour in-memory JWKS cache; raises
  HTTP 401 for missing/expired/invalid tokens
- api/app/auth/user_context.py: get_current_db_user resolves token payload to
  internal User ORM object; get_current_user_id returns User.id (uuid.UUID)
- api/app/services/user_service.py: get_or_create_user — looks up User by
  auth_provider_id, creates new observer-role User on first login; uses
  flush() not commit() to stay within the request transaction
- POST /v1/sightings/ and POST /v1/species/ now require a valid Auth0 token;
  GET endpoints remain public
- api/tests/conftest.py: authenticated_client fixture overrides both get_db
  (transactional rollback) and get_current_user (fake payload) for testing
  authenticated endpoints without a real token
- test_create_species_returns_201 updated to use authenticated_client

### Bugs caught and fixed
- Auth0 sub claims are strings like "auth0|64abc..." not UUIDs — original
  uuid.UUID(user_id) cast would have raised ValueError at runtime; fixed by
  looking up/creating the internal User record and returning User.id instead

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