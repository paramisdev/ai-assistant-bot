from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from pydantic import SecretStr

from bot.config import Settings
from bot.services.llm import (
    LLMAuthError,
    LLMClient,
    LLMConnectionError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTokenLimitError,
)


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "bot_token": SecretStr("test-bot-token"),
        "llm_api_key": SecretStr("secret-key"),
        "llm_api_url": "https://example.com/v1/chat/completions",
        "llm_model": "test-model",
        "llm_timeout_seconds": 5,
        "llm_max_input_chars": 1000,
        "llm_max_chunk_chars": 100,
        "llm_temperature": 0.2,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def make_client(
    response: httpx.Response | None = None,
    *,
    settings: Settings | None = None,
) -> tuple[LLMClient, Mock]:
    http_client = Mock()
    http_client.post = AsyncMock(
        return_value=response
        or httpx.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}]},
        ),
    )
    client = LLMClient(settings or make_settings(), http_client=http_client)
    return client, http_client


@pytest.mark.asyncio
async def test_complete_sends_secret_and_returns_content() -> None:
    response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "  generated answer  "}}]},
    )
    client, http_client = make_client(response, settings=make_settings(llm_model="custom-model"))

    result = await client.complete("hello", system_prompt="system")

    assert result == "generated answer"
    http_client.post.assert_awaited_once()
    _, kwargs = http_client.post.await_args
    assert kwargs["headers"]["Authorization"] == "Bearer secret-key"
    assert kwargs["json"]["model"] == "custom-model"
    assert kwargs["json"]["messages"] == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "hello"},
    ]


@pytest.mark.asyncio
async def test_complete_maps_rate_limit_error() -> None:
    client, _ = make_client(httpx.Response(429, json={"error": "rate limit"}))

    with pytest.raises(LLMRateLimitError):
        await client.complete("hello")


@pytest.mark.asyncio
async def test_complete_maps_token_limit_error() -> None:
    response = httpx.Response(
        400,
        json={"error": {"message": "maximum context length exceeded"}},
    )
    client, _ = make_client(response)

    with pytest.raises(LLMTokenLimitError):
        await client.complete("hello")


@pytest.mark.asyncio
async def test_complete_rejects_text_above_local_limit() -> None:
    client, _ = make_client(settings=make_settings(llm_max_input_chars=5))

    with pytest.raises(LLMTokenLimitError):
        await client.complete("too long")


@pytest.mark.asyncio
async def test_complete_maps_auth_error() -> None:
    client, _ = make_client(httpx.Response(401, json={"error": "invalid key"}))

    with pytest.raises(LLMAuthError):
        await client.complete("hello")


@pytest.mark.asyncio
async def test_complete_maps_server_error_to_connection_error() -> None:
    client, _ = make_client(httpx.Response(503, json={"error": "unavailable"}))

    with pytest.raises(LLMConnectionError):
        await client.complete("hello")


@pytest.mark.asyncio
async def test_complete_maps_unknown_error() -> None:
    client, _ = make_client(httpx.Response(418, json={"error": "teapot"}))

    with pytest.raises(LLMResponseError):
        await client.complete("hello")


@pytest.mark.asyncio
async def test_complete_maps_transport_error() -> None:
    client, http_client = make_client()
    http_client.post.side_effect = httpx.ConnectError("connection failed")

    with pytest.raises(LLMConnectionError):
        await client.complete("hello")


@pytest.mark.asyncio
async def test_complete_rejects_invalid_response_shape() -> None:
    client, _ = make_client(httpx.Response(200, json={"unexpected": []}))

    with pytest.raises(LLMResponseError):
        await client.complete("hello")


@pytest.mark.asyncio
async def test_summarize_short_text_uses_one_request() -> None:
    response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "short summary"}}]},
    )
    client, http_client = make_client(response)

    result = await client.summarize("short text")

    assert result == "short summary"
    http_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_summarize_long_text_splits_and_merges_chunks() -> None:
    response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "summary"}}]},
    )
    client, http_client = make_client(response, settings=make_settings(llm_max_chunk_chars=10))

    result = await client.summarize("a" * 25)

    assert result == "summary"
    assert http_client.post.await_count == 4
