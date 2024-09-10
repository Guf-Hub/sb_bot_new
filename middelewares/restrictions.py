import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from structures.restrictions import Restrictions as Rest


class RestrictionsMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:

        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id
        user_name = event.from_user.username
        message_id = event.message_id

        if event.photo or event.video:
            file_size = event.photo[-1].file_size if event.photo else event.video.file_size
            check_size = Rest.FILE_PHOTO_SIZE if event.photo else Rest.FILE_SIZE

            if file_size > check_size:
                await self._handle_file_too_big(event, message_id, user_name, user_id, file_size, check_size)
                return

        try:
            await handler(event, data)
        except Exception as e:
            logging.exception(f'An error occurred in the handler: {e}')
            # Handle the exception appropriately

    @staticmethod
    async def _handle_file_too_big(event, message_id, user_name, user_id, file_size, check_size):
        logging.error(f'FileIsTooBig > {message_id=} от: {user_name=}, {user_id=} {file_size=} / {check_size=}')
        await event.answer(
            text=f'Файл слишком большой!!!\nРазрешено: 5МБ для фото, 20МБ для остальных файлов.',
            allow_sending_without_reply=True
        )
