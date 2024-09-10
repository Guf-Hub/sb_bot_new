from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message, TelegramObject
from aiogram.dispatcher.flags import get_flag
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, storage: RedisStorage):
        self.storage = storage

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: Message,
                       data: Dict[str, Any]
                       ) -> Any:
        user = f'user{event.from_user.id}'

        check_user = await self.storage.redis.get(name=user)

        if check_user:
            if int(check_user.decode()) == 1:
                await self.storage.redis.set(name=user, value=0, ex=10)
                return await event.answer('Мы обнаружили подозрительную активность. Ждите 10 секунд.')
            return
        await self.storage.redis.set(name=user, value=1, ex=10)

        return await handler(event, data)


class ThrottlingSimpleMiddleware(BaseMiddleware):
    def __init__(self, throttle_time_spin: int, throttle_time_other: int):
        self.caches = {
            "spin": TTLCache(maxsize=10_000, ttl=throttle_time_spin),
            "default": TTLCache(maxsize=10_000, ttl=throttle_time_other)
        }

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        # user = f'user{event.from_user.id}'
        throttling_key = get_flag(data, "throttling_key")
        if throttling_key is not None and throttling_key in self.caches:
            if event.chat.id in self.caches[throttling_key]:
                return await event.answer('Мы обнаружили подозрительную активность. Ждите 10 секунд.')
            else:
                self.caches[throttling_key][event.chat.id] = None
        return await handler(event, data)

    # async def on_process_message(self, message: Message, data: Dict[str, Any]):
    #     throttling_key = get_flag(data, "throttling_key")
    #     if throttling_key is not None and throttling_key in self.caches:
    #         if message.chat.id in self.caches[throttling_key]:
    #             return
    #         else:
    #             self.caches[throttling_key][message.chat.id] = None
