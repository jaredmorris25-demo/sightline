# Sightline — Claude Code Project Context

> This file is read automatically by Claude Code at the start of every session.
> It is the single source of truth for project context, decisions, and current state.
> Update it at the end of every session. Do not let it go stale.

---

## What is Sightline?

Sightline is a field observation platform where anyone can log sightings of wildlife,
flora, fungi, and natural phenomena. Think iNaturalist, but built from scratch as a
learning vehicle for full-stack software engineering on Azure.

The long-term vision is a national-scale biodiversity record — an "Atlas of Living
Australia" equivalent — designed for interoperability and multi-tenancy from day one.

This is NOT a commercial project. It exists to develop engineering capability across
API design, cloud infrastructure, spatial data, time-series, DevSecOps, and mobile.

**Owner:** Director, Data Engineering (government sector, Azure/Databricks background)
**Horizon:** 12 months active development
**Current Phase:** Phase 3 — Web frontend (in progress)

---

## Guiding Design Principles

1. **API-first.** The REST API is the product. Web and mobile are clients. Never couple
   them. Build every endpoint as if the frontend doesn't exist.

2. **Darwin Core alignment.** Sightline's canonical schema must be mappable to/from
   Darwin Core (DwC) — the TDWG public domain standard for biodiversity occurrence data.
   Used by GBIF, iNaturalist, and the Atlas of Living Australia.
   Reference: https://dwc.tdwg.org/terms/

3. **Three-layer ingest model.** Data enters Sightline in three layers:
   - INGEST: accepts any format (Darwin Core archive, CSV, Shapefile, raw JSON, future PDF)
   - MAPPING: rules-based + AI-assisted normalisation to canonical schema
   - CANONICAL: validated, queryable, interoperable internal store
   The original source record is always preserved alongside the mapped canonical record.
   This prevents the "MHR PDF problem". Never delete raw ingest records.

4. **Multi-tenancy by design.** The platform supports Groups — bounded communities of
   users who share sightings, run campaigns, or collaborate on surveys.
   Every sighting has a visibility level: private | group | public.

5. **Device timestamp as source of truth.** For all media and sightings, the device/EXIF
   timestamp and GPS captured at observation time are authoritative. Server receipt time
   (synced_at) is stored separately and never overwrites observed_at. See ADR-003.

6. **Config over hardcode.** ALL environment-specific values live in environment variables
   or Azure Key Vault. Local, dev, staging, prod differ only by config.

7. **IaC for everything.** No Azure resources created manually in the portal.
   All infrastructure defined in Terraform under /infra/.
   State in Azure Blob Storage (stsightlinetfstate, rg-sightline, australiaeast).

8. **Schema discipline.** All migrations tracked with Alembic. No ad-hoc schema changes.
   ERDs maintained in /docs/erd/. Every migration reviewed before apply.

9. **Security by design.** Auth (JWT via Auth0) on all non-public endpoints.
   Secrets never in source or committed .env files.

10. **Document the decision.** ADRs in /docs/adr/. Add one for every significant
    technical choice.

11. **Test as you build.** Every endpoint gets a test before considered complete.
    Tests in /api/tests/ mirroring src structure.

12. **DEVLOG discipline.** Add entry to /docs/DEVLOG.md at end of every session.

13. **Idempotent writes.** All seed scripts, ingest pipelines, and bulk operations must
    be safe to re-run. Use INSERT ... ON CONFLICT DO NOTHING or equivalent upsert
    patterns. Never assume a write hasn't already happened.

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| API | FastAPI (Python 3.12+) | OpenAPI/Swagger built in |
| Database | PostgreSQL 16 + PostGIS | Azure Database for PostgreSQL Flexible Server |
| Spatial ORM | GeoAlchemy2 | PostGIS geometry columns in SQLAlchemy |
| Migrations | Alembic | All schema changes tracked |
| Search | Azure AI Search | Phase 4 — not yet built |
| Media storage | Azure Blob Storage + CDN | Phase 5 — not yet built |
| Auth | Auth0 | OAuth2/OIDC, RS256 JWT, social login — ACCEPTED ADR-001 |
| Web frontend | Next.js 16.2.3 (App Router) | Auth0 v4, react-map-gl v8, Mapbox |
| Mobile (Phase 6) | React Native / Expo | Same API, no backend changes needed |
| Containers | Docker + Docker Compose | Local dev; prod on Azure Container Apps |
| IaC | Terraform (AzureRM provider) | State in Azure Blob Storage |
| CI/CD | GitHub Actions | lint + test on every push — ACTIVE |
| Secrets | Azure Key Vault | Phase 2+ — not yet wired |
| Async / events | Azure Service Bus | Phase 5 — not yet built |
| IDE | VSCode + Claude Code extension | |

---

## Repository Structure

```
sightline/
├── api/                        # FastAPI application
│   ├── app/
│   │   ├── main.py             # App entrypoint, router registration
│   │   ├── config.py           # pydantic-settings (env vars)
│   │   ├── auth/               # Auth0 JWT middleware
│   │   │   ├── dependencies.py # get_current_user, JWKS cache
│   │   │   └── user_context.py # get_current_db_user, get_current_user_id
│   │   ├── models/             # SQLAlchemy ORM models (8 entities)
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── routers/            # Route handlers
│   │   │   ├── sightings.py    # /v1/sightings
│   │   │   ├── species.py      # /v1/species
│   │   │   └── users.py        # /v1/users
│   │   ├── services/           # Business logic
│   │   │   ├── sighting_service.py
│   │   │   ├── species_service.py
│   │   │   └── user_service.py # get_or_create_user
│   │   ├── db/                 # DB session, base
│   │   └── ingest/             # Ingest layer (Phase 5)
│   ├── tests/
│   │   ├── conftest.py         # Rollback fixture, authenticated_client fixture
│   │   ├── test_health.py
│   │   ├── test_species.py
│   │   └── test_auth.py
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
│
├── web/                        # Next.js 16.2.3 frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # Landing page — Mapbox map + sightings markers
│   │   │   ├── layout.tsx      # Root layout, Auth0 session, user provisioning
│   │   │   ├── species/        # Species browser + detail pages
│   │   │   └── api/auth/       # Auth0 route handlers
│   │   ├── lib/
│   │   │   ├── api.ts          # Typed API client (axios)
│   │   │   └── auth0.ts        # Auth0 client with audience config
│   │   └── proxy.ts            # Auth0 v4 middleware
│   └── .env.local              # gitignored — contains secrets
│
├── mobile/                     # React Native / Expo (Phase 6)
│
├── infra/                      # Terraform
│   └── main.tf                 # Backend configured, provider installed
│
├── db/
│   ├── alembic/
│   │   ├── env.py              # include_object filter for PostGIS tables
│   │   └── versions/
│   │       └── 5d17857927af_initial_schema.py
│   ├── alembic.ini
│   └── seed/
│       └── seed_species.py     # 255 Australian species from ALA (idempotent)
│
├── docs/
│   ├── DEVLOG.md
│   ├── PROJECT_BRIEF.md
│   ├── adr/
│   │   ├── 000-template.md
│   │   ├── 001-auth-provider.md       # Auth0 — ACCEPTED
│   │   ├── 002-repo-structure.md      # Monorepo — ACCEPTED
│   │   ├── 003-offline-capture.md     # Device timestamps — ACCEPTED
│   │   └── 004-api-versioning.md      # URI /v1/ — ACCEPTED
│   └── erd/
│       └── schema.md
│
├── .github/workflows/
│   ├── api-ci.yml              # ACTIVE — lint + test on push
│   ├── web-ci.yml              # Placeholder
│   └── infra-plan.yml          # Placeholder
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── CLAUDE.md
└── README.md
```

---

## Project Phases

| Phase | Name | Status | Summary |
|---|---|---|---|
| 1 | Foundation | Complete | Repo, Docker Compose, FastAPI skeleton, Terraform bootstrap |
| 2 | Core API | Complete | Models, migrations, endpoints, auth, seed data, CI |
| 3 | Web frontend | In progress | Map live, species browser, auth working, submit form pending |
| 4 | Search + discovery | Pending | Azure AI Search, spatial queries, heatmaps |
| 5 | Async pipelines | Pending | Service Bus, media processing, Databricks |
| 6 | Mobile app | Pending | React Native/Expo, camera, GPS, offline |

**Current phase:** Phase 3 complete — moving to Phase 4
**Completed:** Full Phase 3 — map, species browser, auth, user provisioning,
  submit form, first real sighting confirmed end-to-end
**Next actions:**
  1. Deploy API to Azure Container Apps (unblocks mobile testing)
  2. Azure Database for PostgreSQL Flexible Server
  3. Azure AI Search for species/sightings discovery
  4. Heatmaps and time-series on web frontend

---

## Live API Endpoints

```
GET  /health                          — ops, unversioned
GET  /ready                           — ops, unversioned
GET  /v1/sightings/                   — public, paginated
POST /v1/sightings/                   — auth required
GET  /v1/sightings/nearby             — public, spatial query
GET  /v1/sightings/{sighting_id}      — public
GET  /v1/species/                     — public, paginated
POST /v1/species/                     — auth required
GET  /v1/species/search               — public, ?q= search
GET  /v1/species/{species_id}         — public
POST /v1/users/me                     — auth required, auto-provisions user
```

Swagger UI: http://localhost:8000/docs

---

## Core Data Entities (Canonical Schema)

### User
Internal only. Fields: id (uuid), display_name, email, auth_provider,
auth_provider_id (indexed), bio, location_home (geometry), avatar_url,
role (observer|curator|admin), created_at, updated_at

### Group
Multi-tenancy foundation. Fields: id (uuid), name, slug (indexed, unique),
description, group_type (class|team|org|campaign|open), owner_id (fk user),
is_public, join_policy (open|invite|approval), created_at, updated_at

### GroupMembership
Fields: id, group_id, user_id, role (member|moderator|admin), joined_at

### Sighting
DwC: Occurrence. Fields: id (uuid), user_id, group_id (nullable), species_id,
observed_at, geometry (PostGIS point SRID 4326, GIST indexed),
location_description, count, behaviour_notes,
visibility (private|group|public), verified, verified_by, created_at

### Species
DwC: Taxon. Note: class_name / order_name (Python reserved words).
Fields: id (uuid), common_name, scientific_name (unique, indexed),
kingdom, phylum, class_name, order_name, family, genus,
inaturalist_id, gbif_id, ala_id, conservation_status, description, created_at

### Location
DwC: Location. Relationship to Sighting is via PostGIS spatial join — NOT FK.
Fields: id (uuid), name, slug (unique), geometry (PostGIS SRID 4326, GIST indexed),
location_type (park|reserve|marine|urban|rural), country, region, description

### Media
Device timestamp is source of truth — see ADR-003.
Fields: id (uuid), sighting_id (nullable — null = draft), user_id,
status (draft|attached|processing|ready), blob_url, cdn_url,
media_type (photo|audio|video), file_size, mime_type, exif_data (JSONB),
observed_at_device (immutable), exif_lat, exif_lng, gps_stripped,
synced_at, uploaded_at

### IngestRecord
NEVER delete these rows. NEVER add delete logic.
Fields: id (uuid), source_format (dwc|csv|shapefile|json|pdf|api),
source_system, source_reference, raw_payload (JSONB, immutable),
group_id (nullable), submitted_by, submitted_at, mapped_at (nullable),
mapping_confidence (0.0-1.0), mapping_notes,
canonical_sighting_id (nullable fk → Sighting)

---

## Auth0 Configuration

- Tenant domain: dev-kr7ljpg5onbkey04.us.auth0.com
- Application: Sightline Web (SPA)
- API audience: https://api.sightline.app
- Algorithm: RS256
- Scopes: read:sightings, write:sightings
- Callback URLs registered: http://localhost:3000/api/auth/callback
- Auth0 v4 for Next.js — breaking changes from v3, see Notes for Claude Code

---

## Environment Variables (never commit values)

```
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/sightline
DATABASE_URL_SYNC=postgresql://user:pass@host:5432/sightline

# Auth0
AUTH0_DOMAIN=dev-kr7ljpg5onbkey04.us.auth0.com
AUTH0_API_AUDIENCE=https://api.sightline.app
AUTH0_CLIENT_ID=WN9aqjcky6ILPh5fBZa0Pf5M9nRTBZca
AUTH0_CLIENT_SECRET=
AUTH0_ALGORITHMS=["RS256"]

# Web (.env.local)
AUTH0_SECRET=
AUTH0_BASE_URL=http://localhost:3000
AUTH0_DOMAIN=dev-kr7ljpg5onbkey04.us.auth0.com
AUTH0_CLIENT_ID=WN9aqjcky6ILPh5fBZa0Pf5M9nRTBZca
AUTH0_CLIENT_SECRET=
AUTH0_AUDIENCE=https://api.sightline.app
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAPBOX_TOKEN=

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=
AZURE_STORAGE_CONTAINER_SIGHTINGS=sightings-media
AZURE_STORAGE_CONTAINER_INGEST=ingest-raw
AZURE_CDN_ENDPOINT=

# Azure Service Bus
AZURE_SERVICEBUS_CONNECTION_STRING=
AZURE_SERVICEBUS_QUEUE_MEDIA=media-processing

# Azure AI Search
AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_API_KEY=
AZURE_SEARCH_INDEX_SPECIES=species
AZURE_SEARCH_INDEX_SIGHTINGS=sightings

# App
ENVIRONMENT=local
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

---

## Branching Strategy

```
main        ← production-ready only, protected, requires PR
develop     ← integration branch
feature/*   ← feature branches off develop
fix/*       ← bug fixes
infra/*     ← terraform changes
docs/*      ← documentation only
```

---

## Development Environments

| Environment | Where | Purpose |
|---|---|---|
| local | macOS via Docker Compose + npm run dev | Day-to-day development |
| dev | Azure | Auto-deployed from develop branch |
| staging | Azure | Pre-prod validation |
| prod | Azure | Live public environment |

**Local services:**
- PostgreSQL/PostGIS: localhost:5432 (Docker)
- pgAdmin: http://localhost:5050 (Docker)
- FastAPI: http://localhost:8000 (Docker, hot-reload)
- Next.js: http://localhost:3000 (npm run dev — must be started manually)

**Azure resources provisioned:**
- Resource group: rg-sightline (australiaeast)
- Storage account: stsightlinetfstate (Terraform state backend)
- Blob container: tfstate

---

## Current State (update this block each session)

**Last updated:** 2026-04-15
**Current phase:** Phase 3 — Web frontend
**Completed:**
  Phase 1: Repo, Docker Compose, FastAPI skeleton, Terraform bootstrap
  Phase 2: SQLAlchemy models (8 entities), Alembic migration, Pydantic schemas,
    species + sightings + users endpoints, Auth0 JWT middleware, get_or_create_user,
    species seed (255 Australian species from ALA), GitHub Actions CI green
  Phase 3 (partial): Next.js scaffold, Mapbox map, species browser, Auth0 login,
    user auto-provisioning confirmed working end-to-end
**In progress:** Phase 3 remaining items
**Blocked by:** Nothing
**Next actions:**
  1. Fix duplicate Login button in nav
  2. Build submit a sighting form (/submit)
  3. Build group pages (/groups, /groups/[slug])
  4. Connect map markers to real sightings data with popups
  5. Commit and push all Phase 3 frontend work
  6. Update CI to include web lint/build check

---

## Architecture Decision Records

| ADR | Title | Status |
|---|---|---|
| 001 | Auth provider — Auth0 | Accepted |
| 002 | Monorepo structure | Accepted |
| 003 | Offline capture — device timestamps as source of truth | Accepted |
| 004 | API versioning — URI /v1/, no trailing slash | Accepted |

---

## Notes for Claude Code

- Always read /docs/DEVLOG.md before starting — check last 3 entries minimum
- Always check /docs/adr/ before making architectural decisions
- New API endpoints follow the pattern in /api/app/routers/
- Schema changes always via Alembic migration — never alter tables directly
- All config via pydantic-settings in /api/app/config.py — no scattered os.environ
- Darwin Core field equivalents go in model docstrings
- IngestRecord rows are permanent — never add delete logic for this model
- Group visibility (private|group|public) must be applied in ALL sighting query filters
- Species model: use class_name and order_name (class and order are reserved in Python)
- All geometry columns use SRID 4326 (WGS84). PostGIS: ST_MakePoint(longitude, latitude)
  — longitude FIRST. All PostGIS function calls require func. prefix in SQLAlchemy.
- Media.observed_at_device comes from EXIF — never overwrite after creation
- Sighting.observed_at should be populated from Media.observed_at_device where available
- All seed scripts and bulk inserts must use upsert patterns (ON CONFLICT DO NOTHING)
- Router endpoints with write side-effects must call await db.commit() — db.flush() in
  services does not commit. Missing commit = silent rollback on request end.
- Auth0 sessions created without audience parameter issue opaque tokens not JWTs.
  Always clear browser cookies and re-login after Auth0 config changes.
- Auth0 v4 Next.js breaking changes from v3: AUTH0_DOMAIN not AUTH0_ISSUER_BASE_URL,
  Auth0Provider renamed, proxy.ts not middleware.ts, react-map-gl/mapbox subpath
  required, use client wrapper components for map (Turbopack disallows ssr:false in
  server components)
- Alembic autogenerate picks up PostGIS system tables — include_object filter in
  db/alembic/env.py handles this. Never remove that filter.
- PYTHONPATH must be set explicitly in CI (PYTHONPATH: .) and Docker exec
  (PYTHONPATH=/app) — uvicorn sets it automatically but pytest does not.
- Next.js dev server must be started manually with npm run dev from web/ directory.
  It does not run as a Docker service. Use a dedicated terminal and keep it open.
- When uncertain, add to Open Questions below and flag in your response

---

## Backlog / Future Ideas

- Classroom mode UI: teacher dashboard with live class sightings map (Phase 3+)
- Gamification: badges, streaks, leaderboards within a Group (Phase 3+)
- Species ID from photo: Azure AI Vision or iNaturalist API (Phase 4-5)
- Offline-first mobile: draft sightings locally, sync when online. See ADR-003 (Phase 6)
- Public Darwin Core Archive export — GBIF-compatible bulk download (Phase 4+)
- Databricks pipeline consuming sightings stream for population trend analytics (Phase 5)
- Heatmaps and time-series charts on web frontend (Phase 4)
- Push notifications for rare species near user's home location (Phase 6)
- Organisation accounts with bulk ingest API key access (Phase 4+)
- Two-way sync with ALA, eBird, iNaturalist (Phase 4+)
- Moderation queue for curator role (Phase 3+)
- Species seed: Vascular plants returns poor ALA data — investigate GBIF alternative
- Species thumbnails from ALA thumbnailUrl + occurrence_count fields (future migration)
- Fix duplicate Login button in nav (Phase 3 — next session)
- Phase 5 task: Full ALA species taxonomy via GBIF Darwin Core Archive download — first real test of the three-layer ingest model.

---

## Open Questions

- [ ] Map provider for prod — Mapbox free tier sufficient for dev, evaluate at scale
- [ ] Domain name — check sightline.app / sightline.io availability
- [ ] Web CI — activate web-ci.yml with Next.js build check on push
- [ ] Azure Key Vault wiring — currently using .env files, migrate before prod deployment
- [ ] Species seed: investigate correct ALA group name for Vascular plants data quality