# ADR-003 — Offline capture: device timestamps as source of truth

**Date:** 2026-04-07
**Status:** Accepted

## Context
Mobile users will frequently log sightings in remote locations without network
connectivity — national parks, coastlines, bushland. The device captures the
photo, GPS coordinates, and timestamp at the moment of observation. Server
receipt may be hours or days later when connectivity is restored.

## Decision
- Media.observed_at_device stores the timestamp from device/EXIF at capture time
- Media.synced_at stores the time the server received the upload
- Media.exif_lat and Media.exif_lng store GPS coordinates extracted from EXIF
- Sighting.observed_at is populated from observed_at_device where available,
  never from server receipt time
- observed_at_device is immutable after creation — never overwrite it

## Rationale
A sighting logged offline in Kakadu and synced three days later in Sydney should
show the Kakadu time and location, not the Sydney airport timestamp. This is the
correct scientific record and matches how reference platforms like iNaturalist
and GBIF handle occurrence timestamps.

## Alternatives rejected
- Using created_at as observed_at — loses accuracy for any offline use case
- Requiring connectivity at time of submission — excludes legitimate field use
```

---

**3. Check ADR-001 and ADR-002**

Claude Code generated these automatically but they likely have placeholder content. Open both and check — if they're empty or generic, either fill them in or add a note `Status: Draft — content pending`. Claude Code will read them and a half-filled ADR is better than a misleading one.

---

**4. One thing to add to CLAUDE.md before running**

In the Notes for Claude Code section, add one line:
```
- Alembic is configured in /db/ not /api/ — run alembic commands from the db/ directory