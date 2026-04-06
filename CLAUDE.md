# Sightline — Claude Code Project Context

> This file is read automatically by Claude Code at the start of every session.
> It is the single source of truth for project context, decisions, and current state.
> Update it at the end of every session. Do not let it go stale.

---

## What is Sightline?

flora, fungi, and natural phenomena. Think iNaturalist, but built from scratch as a
learning vehicle for full-stack software engineering on Azure.

The long-term vision is a national-scale biodiversity record — an "Atlas of Living
Australia" equivalent — designed for interoperability and multi-tenancy from day one.

This is NOT a commercial project. It exists to develop engineering capability across
API design, cloud infrastructure, spatial data, time-series, DevSecOps, and mobile.

**Owner:** Director, Data Engineering (government sector, Azure/Databricks background)
**Horizon:** 12 months active development
**Current Phase:** Phase 1 — Foundation (repo, local dev environment, IaC scaffolding)

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

5. **Config over hardcode.** ALL environment-specific values live in environment variables
   or Azure Key Vault. Local, dev, staging, prod differ only by config. Never hardcode
   connection strings, endpoints, API keys, or feature flags.

6. **IaC for everything.** No Azure resources are created manually in the portal.
   All infrastructure is defined in Terraform under /infra/. Terraform state lives in
   Azure Blob Storage backend.

7. **Schema discipline.** All database migrations tracked with Alembic. No ad-hoc schema
   changes ever. ERDs maintained in /docs/erd/. Every migration reviewed before apply.

8. **Security by design.** Public endpoints sit behind Azure API Management or similar
   gateway. Auth (JWT via Auth0) on all non-public endpoints. Secrets never in source
   or .env files committed to repo. .env.example contains keys only, never values.

9. **Document the decision.** Architectural decisions are recorded as ADRs in /docs/adr/.
   Format: context → decision → rationale → alternatives rejected. Add one whenever a
   significant technical choice is made.

10. **Test as you build.** Not strict TDD, but every API endpoint and data function gets
    a test before it is considered complete. Tests live in /api/tests/ mirroring src structure.

11. **DEVLOG discipline.** Add an entry to /docs/DEVLOG.md at the end of every session.
    What was built, what broke, what was fixed, what was deferred. Future Claude Code
    sessions should read recent DEVLOG entries to understand current state.

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| API | FastAPI (Python 3.12+) | OpenAPI/Swagger built in, aligns with team background |
| Database | PostgreSQL 16 + PostGIS | Azure Database for PostgreSQL Flexible Server |
| Migrations | Alembic | All schema changes tracked |
| Search | Azure AI Search | Species + location discovery |
| Media storage | Azure Blob Storage + CDN | Thumbnail pipeline via Service Bus |
| Auth | Auth0 | OAuth2/OIDC, social login, JWT — decision pending ADR-001 |
| Web frontend | Next.js 14+ (App Router) | Azure Static Web Apps |
| Mobile (Phase 6) | React Native / Expo | Same API, no backend changes needed |
| Containers | Docker + Docker Compose | Local dev; prod on Azure Container Apps |
| IaC | Terraform (AzureRM provider) | State in Azure Blob Storage |
Sightline is a field observation platform where anyone can log sightings of wildlife,
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
│   │   └── 002-repo-structure.md
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
geometry (PostGIS point), location_description, count, behaviour_notes,
visibility (private|group|public), verified, verified_by, created_at
DwC: occurrenceID, eventDate, decimalLatitude, decimalLongitude,
     scientificName, recordedBy, occurrenceStatus, individualCount

### Species
Taxonomic reference. Maps to Darwin Core Taxon.
Fields: id (uuid), common_name, scientific_name, kingdom, phylum, class,
order, family, genus, inaturalist_id, gbif_id, ala_id,
conservation_status, description, created_at
DwC: taxonID, scientificName, kingdom, phylum, class, order,
     family, genus, specificEpithet, vernacularName, taxonRank

### Location
Named places. Maps to Darwin Core Location.
Fields: id (uuid), name, slug, geometry (PostGIS polygon or point),
location_type (park|reserve|marine|urban|rural), country, region, description
DwC: locationID, locality, stateProvince, country,
     decimalLatitude, decimalLongitude, geodeticDatum

### Media
Photos, audio, video attached to sightings.
Fields: id (uuid), sighting_id, user_id, blob_url, cdn_url,
media_type (photo|audio|video), file_size, mime_type,
exif_data (JSONB), gps_stripped, uploaded_at

### IngestRecord
Raw source preservation. NEVER delete these rows.
Fields: id (uuid), source_format (dwc|csv|shapefile|json|pdf|api),
source_system, source_reference, raw_payload (JSONB), group_id (nullable),
submitted_by, submitted_at, mapped_at, mapping_confidence (0.0-1.0),
mapping_notes, canonical_sighting_id (nullable fk to Sighting)

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

---

## Current State (update this block each session)

**Last updated:** 2026-04-06
**Current phase:** Phase 1 complete — moving to Phase 2
**Completed:** Repo scaffold, Docker Compose, FastAPI skeleton with 
  health/ready endpoints, Terraform bootstrap with Azure remote state
**In progress:** Nothing
**Next actions:**
  1. Design database schema and SQLAlchemy models (User, Species, Sighting, 
     Group, Location, Media, IngestRecord)
  2. First Alembic migration
  3. Seed species data from GBIF or ALA
  4. Auth0 setup and JWT middleware

---

## Key External References

- Darwin Core terms: https://dwc.tdwg.org/terms/
- Atlas of Living Australia API: https://api.ala.org.au/
- GBIF API: https://www.gbif.org/developer/summary
- iNaturalist API: https://api.inaturalist.org/v1/docs/
- Auth0 FastAPI quickstart: https://auth0.com/docs/quickstart/backend/python
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
- IngestRecord rows are permanent — never add delete logic for these
- Group visibility (private|group|public) must be applied in ALL sighting query filters
- When uncertain, add to Open Questions below and flag in your response

---

- Heatmaps and time-series charts on web frontend
## Backlog / Future Ideas

Do not build until the relevant phase is reached. Additive, not foundational.

- Classroom mode UI: teacher dashboard with live class sightings map
- Gamification: badges, streaks, leaderboards within a Group
- Species ID from photo (Azure AI Vision or iNaturalist lookup)
- Offline-first mobile: draft sightings locally, sync when online
- Public Darwin Core Archive export (GBIF-compatible bulk download)
- Databricks pipeline consuming sightings stream for population trend analytics
- Push notifications for rare species sighted near user's home location
- Organisation accounts with bulk ingest API key access
- Two-way sync with eBird, iNaturalist, ALA
- Moderation queue for curator role

---

## Open Questions

- [ ] Auth0 vs Azure AD B2C — cost, social login, developer experience
- [ ] Map provider — Mapbox vs Azure Maps vs Leaflet/OSM
- [ ] Species taxonomy seed strategy — GBIF bulk download vs ALA API vs iNaturalist
- [ ] Domain name — check sightline.app / sightline.io availability
- [ ] API versioning — URI (/v1/) vs header-based — decide before first public endpoint
