"""AI interpretation boundary. The shuffle does not import this package."""

from app.ai.base import InterpretationProvider
from app.ai.factory import build_interpretation_provider

__all__ = ["InterpretationProvider", "build_interpretation_provider"]
