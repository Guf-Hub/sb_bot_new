import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler_di import ContextSchedulerDecorator


class SchedulerMiddleware(BaseMiddleware):

    def __init__(self, scheduler: AsyncIOScheduler | ContextSchedulerDecorator):
        self.scheduler = scheduler

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:

        if 'apscheduler' not in data:
            data['apscheduler'] = self.scheduler

        return await handler(event, data)
