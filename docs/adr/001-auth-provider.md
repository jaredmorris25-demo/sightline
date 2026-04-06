# ADR-001: Auth Provider Selection

**Date:** TBD
**Status:** Proposed

---

## Context

Sightline requires authentication and authorisation for all non-public API endpoints.
Key requirements: OAuth2/OIDC, social login (Google, Apple), JWT issuance, multi-tenancy
awareness, developer experience, and cost at low user volumes.

Primary candidates: Auth0, Azure AD B2C.

---

## Decision

TBD — see Open Questions in CLAUDE.md.

---

## Rationale

TBD

---

## Alternatives Rejected

| Alternative | Why rejected |
|---|---|
| Azure AD B2C | TBD |
| Auth0 | TBD |
| Roll-your-own (FastAPI + OAuth2) | Too much undifferentiated work at Phase 1 |

---

## Consequences

TBD
