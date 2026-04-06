# ADR-004: API Versioning Strategy

**Date:** 2026-04-07
**Status:** Accepted

---

## Context

Sightline is a public-facing REST API. A versioning strategy must be decided before
the first domain endpoints are written, as changing URL structure after deployment
is a breaking change for consumers.

---

## Decision

URI versioning using the prefix `/v1/`. No trailing slashes. Ops endpoints
(`/health`, `/ready`) are unversioned. All domain endpoints are prefixed `/v1/`.

Examples: `/v1/sightings`, `/v1/species`, `/v1/groups` — NOT `/health`, `/ready`

---

## Rationale

URI versioning is the most common real-world pattern, used by GBIF, ALA, and
iNaturalist. It is visible in the URL, easy to test in a browser, trivial to
implement in FastAPI via router prefixes. Running v1 and v2 side by side during
a future transition requires no middleware changes — each version is simply a
separate router mounted at a different prefix.

---

## Alternatives Rejected

| Alternative | Why rejected |
|---|---|
| Header versioning (`Accept: application/vnd.sightline.v1+json`) | Harder to test and debug — not visible in browser or curl without extra flags. Adds middleware complexity with no benefit at current scale. |
| Query parameter versioning (`/sightings?version=1`) | Not a recognised standard. Pollutes query parameter namespace. Inconsistent with the APIs Sightline aims to interoperate with (GBIF, ALA, iNaturalist). |

---

## Consequences

- All domain routers in FastAPI are mounted with `prefix="/v1/<resource>"`.
- Ops endpoints (`/health`, `/ready`) remain at root — unversioned by design,
  consumed by infrastructure probes not API clients.
- A future `/v2/` prefix requires no changes to `/v1/` routes — both can run
  concurrently in the same FastAPI app.
- API documentation (OpenAPI/Swagger at `/docs`) will group routes by version tag.
