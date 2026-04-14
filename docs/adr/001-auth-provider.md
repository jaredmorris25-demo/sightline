# ADR-001 — Auth provider

**Date:** 2026-04-07
**Status:** Accepted — Chose to go Auth0; account setup and configured

## Context
Sightline requires authentication for all write endpoints and user identity
management. Two primary candidates evaluated: Auth0 and Azure AD B2C.

## Options under consideration

**Auth0**
- Purpose-built auth platform, excellent developer experience
- FastAPI quickstart documentation is comprehensive
- Social login (Google, Apple) straightforward to configure
- Free tier: 7,500 monthly active users
- Slight vendor lock-in outside Azure ecosystem


## Decision
Auth0 chosen as preferred auth provider

## Notes
Lean toward Auth0 for developer experience and faster Phase 2 progress.
Revisit Azure AD B2C if Azure-native integration becomes a priority in
later phases.