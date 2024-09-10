from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import settings

# Initialize Bot instance with default bot properties which will be passed to all API calls
TOKEN = settings.bot.TELEGRAM_TOKEN_DEV if settings.dev else settings.bot.TELEGRAM_TOKEN
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

__all__ = ('bot',)
