## Title:  Offline capture — device timestamps as source of truth

## Status: Accepted

## Context: 

Mobile users will often be out of connectivity when logging 
  sightings. Device/EXIF timestamp and GPS are captured at observation 
  time, server receipt may be hours or days later.

---

## Decision: 

Media.observed_at_device stores the EXIF/device timestamp 
  and is never overwritten. Media.synced_at stores server receipt time. 
  Sighting.observed_at is populated from observed_at_device, not from 
  created_at.

---

## Rationale: 

A sighting logged offline in a remote location should reflect 
  when and where it was observed, not when connectivity was restored.

---

## Alternatives rejected: 

Using created_at as observed time — loses 
  accuracy for offline use entirely.