"""OpenAI-compatible chat adapter.

Selected only when INTERPRETATION_PROVIDER=openai_compatible. The API key is
read from the environment and is never logged. This adapter is not used by
the shuffle.
"""

import json

import httpx
from pydantic import ValidationError

from app.ai.base import GeneratedInterpretation, InterpretationRequest
from app.ai.prompt_builder import build_messages
from app.domain.errors import TarotError
from app.domain.interpretation import (
    SYMBOLIC_DISCLAIMER,
    StructuredInterpretation,
    render_interpretation_text,
)


class OpenAICompatibleProvider:
    provider_name = "openai_compatible"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.model_name = model
        self.timeout_seconds = timeout_seconds
        self._client = client

    async def generate_reading(
        self,
        request: InterpretationRequest,
    ) -> GeneratedInterpretation:
        if not self.base_url or not self.model_name:
            raise TarotError(
                "The OpenAI-compatible interpreter needs INTERPRETATION_BASE_URL and INTERPRETATION_MODEL.",
                code="provider_not_configured",
            )
        messages = build_messages(request)
        payload = {
            "model": self.model_name,
            "temperature": 0.4,
            "messages": messages.as_chat(),
            "response_format": {"type": "json_object"},
        }
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            response = await self._post(payload, headers)
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except TarotError:
            raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise TarotError(
                "The interpretation provider request failed.",
                code="interpretation_failed",
            ) from exc
        return _from_model_json(
            content,
            provider=self.provider_name,
            model_name=self.model_name,
        )

    async def _post(self, payload: dict, headers: dict[str, str]) -> httpx.Response:
        url = f"{self.base_url}/chat/completions"
        if self._client is not None:
            return await self._client.post(url, json=payload, headers=headers)
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            return await client.post(url, json=payload, headers=headers)


def _from_model_json(content: str, *, provider: str, model_name: str) -> GeneratedInterpretation:
    try:
        payload = json.loads(_strip_fence(content))
        structured = StructuredInterpretation.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise TarotError(
            "The interpretation provider returned an unreadable result.",
            code="interpretation_failed",
        ) from exc
    if SYMBOLIC_DISCLAIMER not in structured.disclaimer:
        structured = structured.model_copy(
            update={
                "disclaimer": f"{structured.disclaimer.rstrip()} {SYMBOLIC_DISCLAIMER}"
            }
        )
    return GeneratedInterpretation(
        provider=provider,
        model_name=model_name,
        interpretation_text=render_interpretation_text(structured),
        structured_result=structured,
    )


def _strip_fence(content: str) -> str:
    text = content.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
