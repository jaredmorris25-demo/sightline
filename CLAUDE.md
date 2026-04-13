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
**Current Phase:** Phase 2 — Core data models and first API endpoints

---

## Guiding Design Principles

These are non-negotiable and must be respected in all code and architecture decisions:

1. **API-first.** The REST API is the product. Web and mobile are clients. Never couple
   them. Build every endpoint as if the frontend doesn't exist.

2. **Darwin Core alignment.** Sightline's canonical schema must be mappable to/from
   Darwin Core (DwC) — the TDWG public domain standard for biodiversity occurrence data.
   Used by GBIF, iNaturalist, and the Atlas of Living Australia. Every core entity
   (Sighting, Species, Location) must have DwC field equivalents documented.
   Reference: https://dwc.tdwg.org/terms/

3. **Three-layer ingest model.** Data enters Sightline in three layers:
   - INGEST: accepts any format (Darwin Core archive, CSV, Shapefile, raw JSON, future PDF)
   - MAPPING: rules-based + AI-assisted normalisation to canonical schema
   - CANONICAL: validated, queryable, interoperable internal store
   The original source record is always preserved alongside the mapped canonical record.
   This prevents the "MHR PDF problem" — unstructured historical data becoming
   permanently inaccessible. Never delete raw ingest records.

4. **Multi-tenancy by design.** The platform supports Groups — bounded communities of
   users who share sightings, run campaigns, or collaborate on surveys. This affects
   the auth model, data ownership model, and query layer. See Group entity below.
   Every sighting has a visibility level: private | group | public.

5. **Device timestamp as source of truth.** For all media and sightings, the device/EXIF
   timestamp and GPS coordinates captured at observation time are the authoritative record.
   Server receipt time (synced_at) is stored separately and never overwrites observed_at.
   This supports offline use in remote locations. See ADR-003.

6. **Config over hardcode.** ALL environment-specific values live in environment variables
   or Azure Key Vault. Local, dev, staging, prod differ only by config. Never hardcode
   connection strings, endpoints, API keys, or feature flags.

7. **IaC for everything.** No Azure resources are created manually in the portal.
   All infrastructure is defined in Terraform under /infra/. Terraform state lives in
   Azure Blob Storage backend (storage account: stsightlinetfstate, rg: rg-sightline).

8. **Schema discipline.** All database migrations tracked with Alembic. No ad-hoc schema
   changes ever. ERDs maintained in /docs/erd/. Every migration reviewed before apply.

9. **Security by design.** Public endpoints sit behind Azure API Management or similar
   gateway. Auth (JWT via Auth0) on all non-public endpoints. Secrets never in source
   or .env files committed to repo. .env.example contains keys only, never values.

10. **Document the decision.** Architectural decisions are recorded as ADRs in /docs/adr/.
    Format: context → decision → rationale → alternatives rejected. Add one whenever a
    significant technical choice is made.

11. **Test as you build.** Not strict TDD, but every API endpoint and data function gets
    a test before it is considered complete. Tests live in /api/tests/ mirroring src structure.

12. **DEVLOG discipline.** Add an entry to /docs/DEVLOG.md at the end of every session.
    What was built, what broke, what was fixed, what was deferred. Future Claude Code
    sessions should read recent DEVLOG entries to understand current state.

13. **Idempotent writes.** All seed scripts, ingest pipelines, and bulk operations 
    must be safe to re-run. Use INSERT ... ON CONFLICT DO NOTHING or equivalent 
    upsert patterns. Never assume a write operation hasn't already run.

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| API | FastAPI (Python 3.12+) | OpenAPI/Swagger built in, aligns with team background |
| Database | PostgreSQL 16 + PostGIS | Azure Database for PostgreSQL Flexible Server |
| Spatial ORM | GeoAlchemy2 | PostGIS geometry columns in SQLAlchemy |
| Migrations | Alembic | All schema changes tracked |
| Search | Azure AI Search | Species + location discovery |
| Media storage | Azure Blob Storage + CDN | Thumbnail pipeline via Service Bus |
| Auth | Auth0 | OAuth2/OIDC, social login, JWT — decision pending ADR-001 |
| Web frontend | Next.js 14+ (App Router) | Azure Static Web Apps |
| Mobile (Phase 6) | React Native / Expo | Same API, no backend changes needed |
| Containers | Docker + Docker Compose | Local dev; prod on Azure Container Apps |
| IaC | Terraform (AzureRM provider) | State in Azure Blob Storage |
| CI/CD | GitHub Actions | lint → test → build → deploy per environment |
| Secrets | Azure Key Vault | Referenced by Container Apps via managed identity |
| Async / events | Azure Service Bus | Media processing pipeline |
| IDE | VSCode + Claude Code extension | |

---

## Repository Structure

```
sightline/
├── api/                        # FastAPI application
│   ├── app/
│   │   ├── main.py             # App entrypoint
│   │   ├── config.py           # Settings via pydantic-settings (env vars)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── routers/            # Route handlers grouped by domain
│   │   ├── services/           # Business logic layer
│   │   ├── db/                 # DB session, base, utilities
│   │   └── ingest/             # Ingest layer (Darwin Core, CSV, etc.)
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── web/                        # Next.js frontend (Phase 3)
│   ├── app/
│   ├── components/
│   ├── public/
│   └── Dockerfile
│
├── mobile/                     # React Native / Expo (Phase 6)
│
├── infra/                      # Terraform — all Azure resources
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   ├── modules/
│   │   ├── api/
│   │   ├── database/
│   │   ├── storage/
│   │   └── networking/
│   └── main.tf
│
├── db/                         # Alembic migrations and seed data
│   ├── alembic/
│   ├── alembic.ini
│   └── seed/
│
├── docs/
│   ├── DEVLOG.md               # Reverse-chronological session log
│   ├── PROJECT_BRIEF.md        # Full project brief
│   ├── adr/                    # Architecture Decision Records
│   │   ├── 000-template.md
│   │   ├── 001-auth-provider.md
│   │   ├── 002-repo-structure.md
│   │   └── 003-offline-capture-media-timestamps.md
│   ├── erd/                    # Entity relationship diagrams
│   └── api/                    # API contracts, Postman collections
│
├── .github/
│   └── workflows/
│       ├── api-ci.yml
│       ├── web-ci.yml
│       └── infra-plan.yml
│
├── .env.example                # Keys only, NEVER values
├── .gitignore
├── docker-compose.yml          # Local dev: api + postgres/postgis + pgadmin
├── docker-compose.override.yml # Local overrides (gitignored)
├── CLAUDE.md                   # This file
└── README.md
```

---

## Project Phases

These phases are sequential but not rigid — later phases inform earlier design decisions.
Phases 1–2 are foundational; phases 3–6 are additive and can evolve organically.

| Phase | Name | Status | Summary |
|---|---|---|---|
| 1 | Foundation | Complete | Repo, Docker Compose, FastAPI skeleton, Terraform bootstrap |
| 2 | Core data models + API | In progress | SQLAlchemy models, Alembic migrations, species/sightings/groups endpoints, Auth0 |
| 3 | Web frontend | Pending | Next.js app — map view, sighting feed, species pages, submit form |
| 4 | Search + discovery | Pending | Azure AI Search, full-text + spatial, trending, heatmaps |
| 5 | Async pipelines | Pending | Service Bus media processing, EXIF extraction, Databricks analytics |
| 6 | Mobile app | Pending | React Native/Expo, camera, GPS, offline draft sightings |

**Phase 2 detail — what must be completed before Phase 3:**
- SQLAlchemy models for all 8 entities (User, Group, GroupMembership, Species,
  Sighting, Location, Media, IngestRecord)
- First Alembic migration applied to local PostgreSQL
- Pydantic schemas (request + response) for each entity
- REST endpoints: GET/POST species, GET/POST sightings (with spatial query),
  GET/POST groups, group membership
- Auth0 JWT middleware protecting write endpoints
- Seed data: ~500 Australian species from GBIF or ALA
- GitHub Actions CI running on every push (lint + tests)
- At least one PostGIS spatial query demonstrated (sightings within radius)

---

## Core Data Entities (Canonical Schema)

### User
Platform identity. Internal only — not a Darwin Core concept.
Fields: id (uuid), display_name, email, auth_provider, auth_provider_id,
bio, location_home (geometry point), avatar_url, role (observer|curator|admin),
created_at, updated_at

### Group
A bounded community — classroom, survey team, research org, citizen campaign.
FOUNDATIONAL entity. Multi-tenancy is designed in from day one.
Fields: id (uuid), name, slug, description,
group_type (class|team|org|campaign|open),
owner_id (fk user), is_public, join_policy (open|invite|approval),
created_at, updated_at

### GroupMembership
Fields: id, group_id, user_id, role (member|moderator|admin), joined_at

### Sighting
Primary observation record. Maps to Darwin Core Occurrence.
Fields: id (uuid), user_id, group_id (nullable), species_id, observed_at,
geometry (PostGIS point, SRID 4326), location_description, count,
behaviour_notes, visibility (private|group|public), verified, verified_by,
created_at
DwC: occurrenceID, eventDate, decimalLatitude, decimalLongitude,
     scientificName, recordedBy, occurrenceStatus, individualCount

### Species
Taxonomic reference. Maps to Darwin Core Taxon.
Note: use class_name and order_name — class and order are reserved in Python.
Fields: id (uuid), common_name, scientific_name, kingdom, phylum, class_name,
order_name, family, genus, inaturalist_id, gbif_id, ala_id,
conservation_status (IUCN code), description, created_at
DwC: taxonID, scientificName, kingdom, phylum, class, order,
     family, genus, specificEpithet, vernacularName, taxonRank

### Location
Named places. Maps to Darwin Core Location.
Fields: id (uuid), name, slug, geometry (PostGIS polygon or point, SRID 4326),
location_type (park|reserve|marine|urban|rural), country, region, description
Relationship to Sighting is computed via PostGIS spatial join — NOT a foreign key.
DwC: locationID, locality, stateProvince, country,
     decimalLatitude, decimalLongitude, geodeticDatum

### Media
Device timestamp and GPS are source of truth — see ADR-003 and Principle 5.
Photos, audio, video attached to sightings.
Fields: id (uuid), sighting_id (nullable — null = draft), user_id,
status (draft|attached|processing|ready), blob_url, cdn_url,
media_type (photo|audio|video), file_size, mime_type,
exif_data (JSONB), observed_at_device (from EXIF — never overwrite),
exif_lat, exif_lng (GPS from EXIF), gps_stripped (boolean — privacy),
synced_at (server receipt time), uploaded_at

### IngestRecord
Raw source preservation. NEVER delete these rows. NEVER add delete logic.
Fields: id (uuid), source_format (dwc|csv|shapefile|json|pdf|api),
source_system, source_reference, raw_payload (JSONB — immutable),
group_id (nullable), submitted_by, submitted_at, mapped_at (nullable),
mapping_confidence (0.0-1.0), mapping_notes,
canonical_sighting_id (nullable fk → Sighting)

---

## Environment Variables (never commit values)

```
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/sightline
DATABASE_URL_SYNC=postgresql://user:pass@host:5432/sightline

# Auth
AUTH0_DOMAIN=
AUTH0_API_AUDIENCE=
AUTH0_CLIENT_ID=
AUTH0_CLIENT_SECRET=

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
ENVIRONMENT=local  # local | dev | staging | prod
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

---

## Branching Strategy

```
main        ← production-ready only, protected, requires PR + review
develop     ← integration branch, all features merge here first
feature/*   ← feature branches off develop
fix/*       ← bug fixes
infra/*     ← terraform / infrastructure changes
docs/*      ← documentation only
```

PRs to develop trigger CI (lint + test).
PRs to main trigger full CI + Terraform plan.
Merges to main trigger production deploy.

---

## Development Environments

| Environment | Where | Purpose |
|---|---|---|
| local | macOS + Windows desktop via Docker Compose | Day-to-day development |
| dev | Azure | Auto-deployed from develop branch |
| staging | Azure | Pre-prod validation |
| prod | Azure | Live public environment |

Local runs identically to cloud via Docker Compose.
All Azure resources have Terraform definitions before they are provisioned.

**Azure resources provisioned so far:**
- Resource group: rg-sightline (australiaeast)
- Storage account: stsightlinetfstate (Terraform state backend)
- Blob container: tfstate

---

## Current State (update this block each session)

**Last updated:** 2026-04-07
**Current phase:** Phase 2 — Core data models
**Completed:** Phase 1 fully complete — repo scaffold, Docker Compose running locally
  (PostgreSQL/PostGIS + pgAdmin + FastAPI), Terraform bootstrap with Azure remote state,
  /health and /ready endpoints live at localhost:8000, full schema designed
**In progress:** SQLAlchemy models and first Alembic migration
**Blocked by:** Nothing
**Next actions:**
  1. Run Claude Code prompt to build SQLAlchemy models for all 8 entities
  2. Review generated Sighting model and migration file before applying
  3. Apply first Alembic migration to local PostgreSQL
  4. Create ADR-003 (offline capture timestamps)
  5. Build Pydantic schemas and first REST endpoints (species, sightings)

---

## Key External References

- Darwin Core terms: https://dwc.tdwg.org/terms/
- Atlas of Living Australia API: https://api.ala.org.au/
- GBIF API: https://www.gbif.org/developer/summary
- iNaturalist API: https://api.inaturalist.org/v1/docs/
- Auth0 FastAPI quickstart: https://auth0.com/docs/quickstart/backend/python
- GeoAlchemy2 docs: https://geoalchemy-2.readthedocs.io/
- PostGIS docs: https://postgis.net/documentation/
- Alembic docs: https://alembic.sqlalchemy.org/
- Terraform AzureRM provider: https://registry.terraform.io/providers/hashicorp/azurerm/latest

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
- All geometry columns use SRID 4326 (WGS84 — standard GPS coordinates)
- Media.observed_at_device comes from EXIF and must never be overwritten after creation
- Sighting.observed_at should be populated from Media.observed_at_device where available
- When uncertain, add to Open Questions below and flag in your response
- Alembic is configured in /db/ not /api/ — run alembic commands from the db/ directory
- When making a significant technical decision during a session, create a draft 
  ADR in /docs/adr/ and flag it in your response for owner review. Do not mark 
  it Accepted — mark it Draft. Owner reviews and accepts in Claude.ai.
- All seed scripts and bulk inserts must use upsert patterns (ON CONFLICT DO NOTHING 
  or DO UPDATE) — never plain INSERT in any script that could be run more than once
- PostGIS autogenerate capturing system tables — fixed with include_object filter
- func. wrapper required on all PostGIS SQLAlchemy calls
- ALA data quality issues handled gracefully by skip logic
- CI needs explicit PYTHONPATH when running outside Docker

---

## Architecture Decision Records

| ADR | Title | Status |
|---|---|---|
| 001 | Auth provider (Auth0 vs Azure AD B2C) | Pending decision |
| 002 | Monorepo structure | Accepted |
| 003 | Offline capture — device timestamps as source of truth | Accepted |

---

## Backlog / Future Ideas

Do not build until the relevant phase is reached. Additive, not foundational.

- Classroom mode UI: teacher dashboard with live class sightings map (Phase 3+)
- Gamification: badges, streaks, leaderboards within a Group (Phase 3+)
- Species ID from photo: Azure AI Vision or iNaturalist API lookup (Phase 4-5)
- Offline-first mobile: draft sightings locally, sync when online. Device timestamp
  and GPS are always source of truth — see ADR-003. (Phase 6)
- Public Darwin Core Archive export — GBIF-compatible bulk download (Phase 4+)
- Databricks pipeline consuming sightings stream for population trend analytics (Phase 5)
- Heatmaps and time-series charts on web frontend (Phase 4)
- Push notifications for rare species sighted near user's home location (Phase 6)
- Organisation accounts with bulk ingest API key access (Phase 4+)
- Two-way sync with ALA, eBird, iNaturalist (Phase 4+)
- Moderation queue for curator role (Phase 3+)
- Seed script: Plants group returns 0 from ALA with speciesGroup:Plants filter. Investigate correct ALA group name — likely Angiosperms or Vascular plants. Re-run seed once fixed.
- ALA response also returns thumbnailUrl, imageUrl, and occurrenceCount. We don't capture those right now but they're genuinely useful — a species thumbnail from ALA would make the web frontend much richer without us managing any images. Worth adding thumbnail_url and occurrence_count fields to the Species model in a future migration.
- Species seed: Vascular plants returns poor data quality from ALA search API — 45/50 records missing scientificName. Investigate ALA species bulk download or alternative endpoint for better plant coverage. Consider GBIF as alternative source for plant taxonomy.

---

## Open Questions

- [ ] Auth0 vs Azure AD B2C — cost, social login, developer experience (resolve in Phase 2)
- [ ] Map provider — Mapbox vs Azure Maps vs Leaflet/OSM (resolve before Phase 3)
- [ ] Species taxonomy seed strategy — GBIF bulk download vs ALA API vs iNaturalist
- [ ] Domain name — check sightline.app / sightline.io availability
- [x] API versioning — URI (/v1/), no trailing slash. Unversioned ops endpoints. See ADR-004.
