from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def get_or_create_user(db: AsyncSession, token_payload: dict) -> User:
    """
    Return the internal User record for an Auth0 token payload.

    Looks up by auth_provider_id (Auth0 sub claim). If no record exists,
    creates one with role=observer. This is the bridge between Auth0 identity
    and Sightline's internal user table.
    """
    sub = token_payload["sub"]

    result = await db.execute(select(User).where(User.auth_provider_id == sub))
    user = result.scalar_one_or_none()

    if user is not None:
        return user

    email: str | None = token_payload.get("email")

    # Derive a display name: prefer the name claim, fall back to email prefix.
    name_claim: str | None = token_payload.get("name")
    if name_claim:
        display_name = name_claim
    elif email:
        display_name = email.split("@")[0]
    else:
        display_name = sub

    user = User(
        auth_provider="auth0",
        auth_provider_id=sub,
        display_name=display_name,
        email=email or f"{sub}@placeholder.sightline.internal",
        role=UserRole.observer,
    )
    db.add(user)
    await db.flush()  # Populate user.id without committing the transaction.
    return user
