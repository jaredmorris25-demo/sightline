# ADR-002 — Monorepo structure

**Date:** 2026-04-07
**Status:** Accepted

## Context
Sightline comprises multiple components — API, web frontend, mobile app,
infrastructure, and documentation. A decision was needed on whether to use
a single repository or separate repositories per component.

## Decision
Single monorepo at github.com/jaredmorris25-demo/sightline containing all
components under /api, /web, /mobile, /infra, /db, /docs.

## Rationale
- Simpler cross-component changes (API + frontend change in one PR)
- Single CI/CD pipeline configuration to maintain
- Easier for a solo developer to navigate and manage
- Documentation and ADRs stay close to the code they describe
- Can always split later if team size warrants it

## Alternatives rejected
- Multi-repo: adds overhead managing multiple remotes, branches, and pipelines
  with no meaningful benefit at current team size and project stage