import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import Settings
from bot.handlers import chat, commands
from bot.services.llm import LLMClient

logger = logging.getLogger(__name__)


async def run_bot(settings: Settings) -> None:
    bot = Bot(token=settings.bot_token.get_secret_value())
    dispatcher = Dispatcher()
    dispatcher.include_router(commands.router)
    dispatcher.include_router(chat.router)

    try:
        async with LLMClient(settings) as llm:
            logger.info("Starting ai-assistant-bot")
            await dispatcher.start_polling(bot, llm=llm)
    finally:
        await bot.session.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings()  # type: ignore[call-arg]
    asyncio.run(run_bot(settings))
