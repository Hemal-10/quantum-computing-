"""Pydantic response/request schemas for the health endpoint."""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Schema returned by GET /api/health."""

    status: str
    version: str
    message: str
