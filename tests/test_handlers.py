from unittest.mock import AsyncMock, Mock

import pytest

from bot.handlers.chat import process_summarize
from bot.handlers.commands import cmd_summarize
from bot.services.llm import LLMConnectionError
from bot.states.chat import SummarizeStates


@pytest.mark.asyncio
async def test_cmd_summarize_sets_waiting_state() -> None:
    message = Mock()
    message.answer = AsyncMock()
    state = Mock()
    state.set_state = AsyncMock()

    await cmd_summarize(message, state)

    state.set_state.assert_awaited_once_with(SummarizeStates.waiting_for_text)
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_summarize_clears_state_after_success() -> None:
    message = Mock()
    message.text = "long text"
    message.answer = AsyncMock()
    state = Mock()
    state.clear = AsyncMock()
    llm = Mock()
    llm.summarize = AsyncMock(return_value="short summary")

    await process_summarize(message, state, llm)

    llm.summarize.assert_awaited_once_with("long text")
    state.clear.assert_awaited_once()
    message.answer.assert_awaited_once_with("short summary")


@pytest.mark.asyncio
async def test_process_summarize_keeps_state_after_api_error() -> None:
    message = Mock()
    message.text = "long text"
    message.answer = AsyncMock()
    state = Mock()
    state.clear = AsyncMock()
    llm = Mock()
    llm.summarize = AsyncMock(side_effect=LLMConnectionError("api down"))

    await process_summarize(message, state, llm)

    state.clear.assert_not_awaited()
    message.answer.assert_awaited_once()
