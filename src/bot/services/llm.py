from __future__ import annotations

from types import TracebackType
from typing import Any, cast

import httpx

from bot.config import Settings
from bot.services.prompts import ASSISTANT_SYSTEM_PROMPT, SUMMARIZE_SYSTEM_PROMPT
from bot.services.text import split_text


class LLMError(Exception):
    """Base class for LLM client errors."""


class LLMConnectionError(LLMError):
    """The LLM API is unavailable or the request timed out."""


class LLMRateLimitError(LLMError):
    """The LLM API rejected the request because of a rate limit."""


class LLMTokenLimitError(LLMError):
    """The text is too long for the model context window."""


class LLMAuthError(LLMError):
    """The API key is invalid or has no access."""


class LLMResponseError(LLMError):
    """The LLM API returned an unexpected response."""


class LLMClient:
    """Async client for OpenAI-compatible chat completion APIs."""

    def __init__(
        self,
        settings: Settings,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._owns_client = http_client is None
        self._http_client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.llm_timeout_seconds),
        )

    async def __aenter__(self) -> LLMClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http_client.aclose()

    async def complete(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        """Send a prompt to the LLM and return the generated text."""
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Prompt must not be empty")
        if len(prompt) > self._settings.llm_max_input_chars:
            raise LLMTokenLimitError(
                "Текст слишком длинный для отправки в нейросеть. "
                "Сократите его или используйте /summarize.",
            )

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self._settings.llm_model,
            "messages": messages,
            "temperature": self._settings.llm_temperature,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.llm_api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }

        try:
            response = await self._http_client.post(
                self._settings.llm_api_url,
                headers=headers,
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise LLMConnectionError(
                "Нейросеть не ответила вовремя. Попробуйте ещё раз позже.",
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMConnectionError(
                "Не удалось подключиться к API нейросети. Попробуйте ещё раз позже.",
            ) from exc

        self._raise_for_status(response)

        try:
            data = cast(dict[str, Any], response.json())
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMResponseError("Нейросеть вернула неожиданный ответ.") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMResponseError("Нейросеть вернула пустой ответ.")

        return content.strip()

    async def ask(self, text: str) -> str:
        """Answer a regular user message."""
        return await self.complete(text, system_prompt=ASSISTANT_SYSTEM_PROMPT)

    async def summarize(self, text: str) -> str:
        """Summarize long text, splitting it into chunks when needed."""
        text = text.strip()
        if not text:
            raise ValueError("Text must not be empty")

        chunk_size = self._settings.llm_max_chunk_chars
        if len(text) <= chunk_size:
            return await self.complete(text, system_prompt=SUMMARIZE_SYSTEM_PROMPT)

        summaries: list[str] = []
        for chunk in split_text(text, chunk_size):
            summary = await self.complete(
                f"Сделай краткую выжимку этого фрагмента:\n\n{chunk}",
                system_prompt=SUMMARIZE_SYSTEM_PROMPT,
            )
            summaries.append(summary)

        combined = "\n\n".join(summaries)
        return await self.complete(
            f"Объедини выжимки в один краткий и связный ответ:\n\n{combined}",
            system_prompt=SUMMARIZE_SYSTEM_PROMPT,
        )

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code == 429:
            raise LLMRateLimitError(
                "Превышен лимит запросов к нейросети. Подождите немного и повторите.",
            )

        if response.status_code in {400, 413} and _looks_like_token_error(response.text):
            raise LLMTokenLimitError(
                "Текст слишком длинный для контекста модели. Сократите его.",
            )

        if response.status_code in {401, 403}:
            raise LLMAuthError(
                "API-ключ нейросети недействителен или не имеет доступа.",
            )

        if response.status_code >= 500:
            raise LLMConnectionError(
                "API нейросети временно недоступно. Попробуйте ещё раз позже.",
            )

        if response.status_code >= 400:
            raise LLMResponseError(
                f"API нейросети вернуло ошибку {response.status_code}.",
            )


def _looks_like_token_error(body: str) -> bool:
    normalized = body.lower()
    markers = (
        "token",
        "context length",
        "maximum context",
        "too many tokens",
        "request too large",
    )
    return any(marker in normalized for marker in markers)
