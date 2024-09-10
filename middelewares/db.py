from typing import Any, Awaitable, Callable, Dict, Union

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message

from sqlalchemy.ext.asyncio import async_sessionmaker

from database import Database
from structures.mw_data_structure import TransferData


class DataBaseSession(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data['db'] = Database(session)
            data['session'] = session
            return await handler(event, data)


class DatabaseMiddleware(BaseMiddleware):
    """This middleware throw a Database class to handler"""

    async def __call__(
            self,
            handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
            event: Union[Message, CallbackQuery],
            data: TransferData,
    ) -> Any:
        async with data["pool"]() as session:
            data['db'] = Database(session)
            data['session'] = session
            return await handler(event, data)
