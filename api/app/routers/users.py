from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.user_context import get_current_db_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter()


@router.post("/me", response_model=UserRead, status_code=200)
async def get_or_create_me(
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Provision (or retrieve) the authenticated user's internal profile.

    Called by the web frontend after login to ensure a User row exists in the
    database. Idempotent — returns the existing record on subsequent calls.
    The actual upsert logic lives in get_or_create_user (user_service.py).
    """
    await db.commit()
    return current_user
