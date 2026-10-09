"""FastAPI application entry point for Quantum DNA Sequence Analyzer."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dna import router as dna_router
from app.api.health import router as health_router
from app.api.quantum import router as quantum_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Factory that builds and configures the FastAPI app."""
    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ---------------------------------------------------------------------------
    # CORS – allow the Vite dev server (and any extra origins from settings)
    # ---------------------------------------------------------------------------
    cors_origins = settings.cors_origin_list
    allow_all = "*" in cors_origins or len(cors_origins) == 0
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else cors_origins,
        allow_credentials=False if allow_all else True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---------------------------------------------------------------------------
    # Root & Health Check Endpoints (for Render health probes)
    # ---------------------------------------------------------------------------
    @app.api_route("/", methods=["GET", "HEAD"], tags=["root"])
    async def root():
        return {
            "status": "ok",
            "message": "Quantum DNA Sequence Analyzer API is running.",
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    @app.api_route("/health", methods=["GET", "HEAD"], tags=["root"])
    async def root_health():
        return {
            "status": "ok",
            "message": "Quantum DNA Sequence Analyzer API is running.",
            "version": settings.APP_VERSION,
        }

    # ---------------------------------------------------------------------------
    # Routers
    # ---------------------------------------------------------------------------
    app.include_router(health_router)
    app.include_router(dna_router)
    app.include_router(quantum_router)

    return app


app = create_app()
