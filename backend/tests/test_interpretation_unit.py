"""Interpretation providers do not choose cards."""

import json

import httpx
import pytest

from app.ai.base import CardReadingContext, InterpretationRequest
from app.ai.factory import build_interpretation_provider
from app.ai.mock_provider import DEMONSTRATION_BANNER, MockInterpretationProvider
from app.ai.openai_compatible import OpenAICompatibleProvider
from app.ai.prompt_builder import build_messages
from app.core.config import Settings
from app.domain.errors import TarotError
from app.domain.interpretation import SYMBOLIC_DISCLAIMER
from pydantic import SecretStr


def _request() -> InterpretationRequest:
    return InterpretationRequest(
        question="What should I know about my relationship?",
        spread_name="Three Card Spread",
        spread_description="Past, present, and future.",
        cards=(
            CardReadingContext(
                position_index=0,
                position_name="Past",
                position_description="What came before.",
                card_id=1,
                card_name="The Fool",
                arcana_type="major",
                suit=None,
                rank="0",
                orientation="upright",
                general_meaning="Development seed meaning for The Fool upright.",
                keywords=("beginnings",),
                love_meaning="love",
                career_meaning="career",
                advice="advice",
            ),
            CardReadingContext(
                position_index=1,
                position_name="Present",
                position_description="What is active.",
                card_id=2,
                card_name="The Magician",
                arcana_type="major",
                suit=None,
                rank="1",
                orientation="reversed",
                general_meaning="Development seed meaning for The Magician reversed.",
                keywords=("will",),
                love_meaning=None,
                career_meaning=None,
                advice=None,
            ),
        ),
    )


def test_prompt_fixes_the_cards_and_states_the_symbolic_limit() -> None:
    messages = build_messages(_request())
    combined = messages.system + messages.user
    assert "must not change" in messages.system
    assert SYMBOLIC_DISCLAIMER in messages.system
    assert "The Fool" in combined
    assert "upright" in combined
    assert "The Magician" in combined
    assert "reversed" in combined
    assert "Past" in combined
    assert "What should I know about my relationship?" in combined


@pytest.mark.asyncio
async def test_mock_provider_is_deterministic_and_labelled() -> None:
    provider = MockInterpretationProvider()
    first = await provider.generate_reading(_request())
    second = await provider.generate_reading(_request())
    assert first == second
    assert first.provider == "mock"
    assert DEMONSTRATION_BANNER in first.interpretation_text
    assert "not an intelligent tarot reading" in first.interpretation_text
    assert first.structured_result.card_interpretations[0].card_name == "The Fool"
    assert first.structured_result.card_interpretations[1].orientation == "reversed"
    assert SYMBOLIC_DISCLAIMER in first.structured_result.disclaimer


def test_factory_defaults_to_the_mock_provider() -> None:
    provider = build_interpretation_provider(Settings(interpretation_provider="mock"))
    assert isinstance(provider, MockInterpretationProvider)


def test_factory_can_build_an_openai_compatible_provider_without_a_hardcoded_key() -> None:
    provider = build_interpretation_provider(
        Settings(
            interpretation_provider="openai_compatible",
            interpretation_base_url="http://localhost:8001/v1",
            interpretation_api_key=SecretStr(""),
            interpretation_model="qwen",
        )
    )
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider._api_key == ""


def test_unknown_provider_is_rejected() -> None:
    with pytest.raises(TarotError) as caught:
        build_interpretation_provider(Settings(interpretation_provider="mystery"))
    assert caught.value.code == "provider_not_configured"


@pytest.mark.asyncio
async def test_openai_compatible_provider_posts_the_prompt_and_parses_json() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization", "")
        body = json.loads(request.content)
        seen["system"] = body["messages"][0]["content"]
        seen["user"] = body["messages"][1]["content"]
        payload = {
            "card_interpretations": [
                {
                    "position_index": 0,
                    "position_name": "Past",
                    "card_name": "The Fool",
                    "orientation": "upright",
                    "interpretation": "A beginning.",
                }
            ],
            "relationships": "One follows another.",
            "overall": "A reflective note.",
            "guidance": "Sit with the symbol.",
            "disclaimer": "Model disclaimer.",
        }
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(payload)}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider(
        base_url="http://models.example/v1",
        api_key="test-key",
        model="qwen",
        timeout_seconds=5,
        client=client,
    )
    generated = await provider.generate_reading(_request())
    await client.aclose()
    assert seen["authorization"] == "Bearer test-key"
    assert "The Fool" in seen["user"]
    assert "must not change" in seen["system"]
    assert generated.provider == "openai_compatible"
    assert SYMBOLIC_DISCLAIMER in generated.structured_result.disclaimer
    assert "test-key" not in generated.interpretation_text


@pytest.mark.asyncio
async def test_openai_provider_without_configuration_does_not_call_the_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("the network must not be called")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider(
        base_url="",
        api_key="",
        model="",
        timeout_seconds=5,
        client=client,
    )
    with pytest.raises(TarotError) as caught:
        await provider.generate_reading(_request())
    await client.aclose()
    assert caught.value.code == "provider_not_configured"


@pytest.mark.asyncio
async def test_openai_provider_reports_rate_limit_without_the_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"message": "rate limited"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider(
        base_url="http://models.example/v1",
        api_key="test-key",
        model="example-model",
        timeout_seconds=5,
        client=client,
    )
    with pytest.raises(TarotError) as caught:
        await provider.generate_reading(_request())
    await client.aclose()
    assert caught.value.code == "interpretation_failed"
    assert caught.value.details["status_code"] == 429
    assert "test-key" not in caught.value.message
