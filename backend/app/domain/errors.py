"""Domain errors.

HTTP status codes are applied at the API boundary. Services and the tarot
engine raise these errors without importing FastAPI.
"""

from typing import Any


class TarotError(Exception):
    """A predictable tarot-domain failure."""

    code = "tarot_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        return self.message
