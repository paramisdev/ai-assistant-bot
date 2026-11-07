from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states.chat import SummarizeStates

router = Router(name="commands")

START_TEXT = (
    "Привет! Я ИИ-ассистент.\n\n"
    "Просто отправьте мне текст — я отвечу на него.\n"
    "Команда /summarize поможет сделать краткую выжимку длинного текста."
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(START_TEXT)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Доступные команды:\n"
        "/start — начать работу\n"
        "/summarize — сделать краткую выжимку текста\n\n"
        "Любое обычное сообщение будет отправлено ИИ-ассистенту.",
    )


@router.message(Command("summarize"))
async def cmd_summarize(message: Message, state: FSMContext) -> None:
    await state.set_state(SummarizeStates.waiting_for_text)
    await message.answer(
        "Пришлите длинный текст одним сообщением, и я сделаю краткую выжимку. "
        "Для отмены отправьте /cancel.",
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие отменено.")
