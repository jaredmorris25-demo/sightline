# ADR-002: Monorepo Structure

**Date:** 2026-04-06
**Status:** Accepted

---

## Context

Sightline has multiple components: API (Python/FastAPI), web frontend (Next.js),
mobile app (React Native/Expo), infrastructure (Terraform), and database migrations
(Alembic). A decision was needed on whether to use a monorepo or separate repos per
component.

---

## Decision

A single monorepo with top-level directories per component (`api/`, `web/`, `mobile/`,
`infra/`, `db/`). CI workflows are component-scoped and only trigger on relevant path changes.

---

## Rationale

- Single source of truth for cross-cutting changes (e.g. schema + API + frontend in one PR)
- Simpler local development: one `git clone`, one `docker-compose up`
- At current team size (1 developer), repo overhead of polyrepo provides no benefit
- GitHub Actions path filters give per-component CI without splitting repos

---

## Alternatives Rejected

| Alternative | Why rejected |
|---|---|
| Separate repo per component | Added overhead, harder to keep API contracts in sync across repos |
| Nx / Turborepo monorepo tooling | Premature at current scale; revisit if Node tooling grows |

---

## Consequences

- CI workflows must use `paths:` filters to avoid unnecessary runs
- Docker images built per component; docker-compose ties them together locally
- Terraform state is per-environment, not per-repo — no structural conflict
