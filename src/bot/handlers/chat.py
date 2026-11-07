from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.services.llm import (
    LLMAuthError,
    LLMClient,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTokenLimitError,
)
from bot.states.chat import SummarizeStates

router = Router(name="chat")


def _llm_error_message(error: LLMError) -> str:
    if isinstance(error, LLMRateLimitError):
        return "Превышен лимит запросов к нейросети. Подождите немного и повторите."
    if isinstance(error, LLMTokenLimitError):
        return "Текст слишком длинный для нейросети. Сократите его и попробуйте снова."
    if isinstance(error, LLMAuthError):
        return "Проблема с доступом к нейросети. Проверьте API-ключ в настройках."
    if isinstance(error, LLMConnectionError):
        return "Нейросеть сейчас недоступна. Попробуйте ещё раз позже."
    if isinstance(error, LLMResponseError):
        return "Нейросеть вернула неожиданный ответ. Попробуйте ещё раз."
    return "Не удалось обработать запрос. Попробуйте ещё раз."


@router.message(SummarizeStates.waiting_for_text, F.text)
async def process_summarize(
    message: Message,
    state: FSMContext,
    llm: LLMClient,
) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Пришлите текст одним сообщением.")
        return

    try:
        summary = await llm.summarize(text)
    except LLMError as error:
        await message.answer(_llm_error_message(error))
        return

    await state.clear()
    await message.answer(summary)


@router.message(F.text & ~F.text.startswith("/"))
async def process_text(message: Message, llm: LLMClient) -> None:
    text = (message.text or "").strip()
    if not text:
        return

    try:
        answer = await llm.ask(text)
    except LLMError as error:
        await message.answer(_llm_error_message(error))
        return

    await message.answer(answer)
