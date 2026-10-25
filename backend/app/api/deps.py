"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import InterpretationProvider
from app.ai.factory import build_interpretation_provider
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.domain.errors import TarotError
from app.domain.random_source import RandomSource, SystemRandomSource
from app.services.interpretation_service import InterpretationService
from app.services.reading_service import ReadingService

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Reading access token returned when the reading was created.",
)


def get_random_source() -> RandomSource:
    return SystemRandomSource()


def get_interpretation_provider(
    settings: Annotated[Settings, Depends(get_settings)],
) -> InterpretationProvider:
    return build_interpretation_provider(settings)


async def require_bearer(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials.strip()
    ):
        raise TarotError(
            "A bearer token is required for this reading.",
            code="unauthorized",
        )
    return credentials.credentials.strip()


async def get_reading_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    rng: Annotated[RandomSource, Depends(get_random_source)],
) -> ReadingService:
    return ReadingService(session, rng)


async def get_interpretation_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    provider: Annotated[InterpretationProvider, Depends(get_interpretation_provider)],
) -> InterpretationService:
    return InterpretationService(session, provider)
