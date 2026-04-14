"""
Auth0 JWT middleware for the Sightline API.

Validates RS256-signed tokens issued by Auth0. The JWKS public key set is
fetched once from Auth0 and cached in memory for 24 hours to avoid a network
round-trip on every request.
"""

from datetime import datetime, timedelta, timezone

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt

from app.config import settings

_security = HTTPBearer()

# In-memory JWKS cache — refreshed every 24 hours.
_jwks_cache: dict = {}
_jwks_fetched_at: datetime | None = None
_JWKS_TTL = timedelta(hours=24)


async def _get_jwks() -> dict:
    """Return the Auth0 JWKS, fetching from the network only if the cache is stale."""
    global _jwks_cache, _jwks_fetched_at

    now = datetime.now(timezone.utc)
    if _jwks_fetched_at is None or (now - _jwks_fetched_at) > _JWKS_TTL:
        url = f"https://{settings.auth0_domain}/.well-known/jwks.json"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_fetched_at = now

    return _jwks_cache


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> dict:
    """
    Validate a Bearer token and return its decoded payload.

    Raises HTTPException(401) for:
    - Missing or malformed Authorization header (handled by HTTPBearer)
    - Expired token
    - Invalid signature
    - Wrong audience or issuer
    - No matching key in JWKS
    """
    token = credentials.credentials

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        )

    try:
        jwks = await _get_jwks()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to fetch token signing keys",
        )

    # Find the key in the JWKS that matches the token's key ID.
    kid = unverified_header.get("kid")
    rsa_key: dict = {}
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
            break

    if not rsa_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find matching signing key",
        )

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=settings.auth0_algorithms,
            audience=settings.auth0_api_audience,
            issuer=f"https://{settings.auth0_domain}/",
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
        )

    return payload
