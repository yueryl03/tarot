"""FastAPI application."""

from contextlib import asynccontextmanager
import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.types import ASGIApp, Message, Receive, Scope, Send

import app.models  # noqa: F401
from app import __version__
from app.api.errors import register_exception_handlers
from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import dispose_engine, get_db
from app.domain.errors import TarotError
from app.schemas.common import HealthResponse

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Add nosniff without BaseHTTPMiddleware.

    Starlette's function middleware runs the endpoint in a child task, which
    breaks asyncpg connections checked out on the request task.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_header(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-content-type-options", b"nosniff"))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_header)

OPENAPI_TAGS = [
    {
        "name": "cards",
        "description": "Public Rider-Waite-Smith catalog. This is not a shuffled deck.",
    },
    {
        "name": "spreads",
        "description": "Database-defined spreads. Draw limits come from card_count.",
    },
    {
        "name": "readings",
        "description": (
            "Create one shuffled 78-card deck and reveal it incrementally. "
            "Unrevealed identities are never returned. Orientation is chosen "
            "at shuffle time."
        ),
    },
    {
        "name": "interpretations",
        "description": (
            "Symbolic interpretation of a completed reading. "
            "The interpreter cannot change the deck."
        ),
    },
    {"name": "health", "description": "Process and database health."},
]

DESCRIPTION = """
Backend for a Rider-Waite-Smith tarot reading.

A reading is one physical deck of 78 cards. Upright and reversed are
orientations, not extra cards. The deck is shuffled once with Fisher-Yates
and `secrets.SystemRandom`, stored, and revealed without reshuffling.

This is an idealised shuffle. A person shuffling real cards does not
necessarily produce a perfectly uniform order or a fair share of reversals.

Before any card is revealed, P(a specific card) = 1/78. With reversals
enabled, orientation is an independent fair coin, so
P(a specific card with a specified orientation) = 1/156 for the first card.
After k cards are revealed, 78-k cards remain. Orientation is not sampled again.

The default interpreter is a labelled mock. It does not choose cards.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info(
        "application_started provider=%s",
        settings.interpretation_provider,
        extra={"operation": "startup"},
    )
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(SecurityHeadersMiddleware)
    register_exception_handlers(app)
    app.include_router(v1_router, prefix="/api/v1")

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"docs": "/docs", "health": "/health", "api": "/api/v1"}

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/health/ready", response_model=HealthResponse, tags=["health"])
    async def ready(
        session: AsyncSession = Depends(get_db),
    ) -> HealthResponse:
        try:
            await session.execute(text("SELECT 1"))
        except Exception as exc:
            logger.exception("readiness_failed", extra={"operation": "ready"})
            raise TarotError(
                "Database is unavailable.",
                code="database_unavailable",
            ) from exc
        return HealthResponse(status="ok")

    return app


app = create_app()
