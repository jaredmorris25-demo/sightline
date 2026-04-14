import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.user_service import get_or_create_user


async def get_current_db_user(
    payload: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the Auth0 token payload to an internal User ORM object."""
    return await get_or_create_user(db, payload)


async def get_current_user_id(
    user: User = Depends(get_current_db_user),
) -> uuid.UUID:
    """Return the internal UUID of the authenticated user."""
    return user.id
