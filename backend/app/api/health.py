"""Health check API router."""
from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health_check() -> HealthResponse:
    """Return service liveness status, version, and a short message."""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        message="Quantum DNA Sequence Analyzer backend is running.",
    )
