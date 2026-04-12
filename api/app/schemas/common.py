from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list envelope used by all list endpoints."""
    items: list[T]
    total: int
    limit: int = Field(..., ge=1, le=200)
    offset: int = Field(..., ge=0)
