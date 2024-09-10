from typing import Any, Awaitable, Callable, Dict, Union

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from sqlalchemy import select

from database import Database
from structures.mw_data_structure import TransferData, TransferUserData
from database.models import User


class RoleMiddleware(BaseMiddleware):
    """
    This class is used for getting user role from database
    """

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Union[TransferUserData, TransferData],
    ) -> Any:
        db: Database = data["db"]  # type : ignore
        user = await db.user.get_one(user_id=event.from_user.id)
        print(user)
        # data["role"] = user.role

        return await handler(event, data)
