"""Choose the interpretation provider from settings."""

from app.ai.base import InterpretationProvider
from app.ai.mock_provider import MockInterpretationProvider
from app.ai.openai_compatible import OpenAICompatibleProvider
from app.core.config import Settings
from app.domain.errors import TarotError


def build_interpretation_provider(settings: Settings) -> InterpretationProvider:
    name = settings.interpretation_provider.strip().lower()
    if name == "mock":
        return MockInterpretationProvider()
    if name == "openai_compatible":
        return OpenAICompatibleProvider(
            base_url=settings.interpretation_base_url,
            api_key=settings.interpretation_api_key.get_secret_value(),
            model=settings.interpretation_model,
            timeout_seconds=settings.interpretation_timeout_seconds,
        )
    raise TarotError(
        "The interpretation provider is not configured.",
        code="provider_not_configured",
        details={"interpretation_provider": settings.interpretation_provider},
    )
