from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db.session import AsyncSessionLocal

app = FastAPI(
    title="Sightline API",
    version="0.1.0",
    description="Field observation platform API — biodiversity occurrence records.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Domain routers registered here as they are built ---
# from app.routers import sightings, species, locations, groups, users, ingest
# app.include_router(sightings.router, prefix="/v1/sightings", tags=["sightings"])


@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok", "environment": settings.environment}


@app.get("/ready", tags=["ops"])
async def ready():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
