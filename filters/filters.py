import logging

from aiogram.filters import Filter
from aiogram.types import Message
from aiogram import Bot

from database import Database, async_session_factory
from core.config import settings
from structures.role import Role


class ChatTypeFilter(Filter):
    def __init__(self, chat_type: str | list[str]) -> None:
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:

        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type


class ActiveFilter(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message, bot: Bot) -> bool:
        async with async_session_factory() as session:
            db = Database(session)
            active = await db.user.is_active(user_id=message.from_user.id)
            if active:
                return True
            else:
                return False


class AdminFilter(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message, bot: Bot) -> bool:
        user_id = message.from_user.id
        if user_id in settings.bot.ADMINS:
            return True
        async with async_session_factory() as session:
            db = Database(session)
            role = await db.user.get_role(user_id=user_id)
            return role == Role.admin


class StaffFilter(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message, bot: Bot) -> bool:
        user_id = message.from_user.id
        async with async_session_factory() as session:
            db = Database(session)
            role = await db.user.get_role(user_id=user_id)
            return role == Role.staff


class SupervisorFilter(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message, bot: Bot) -> bool:
        async with async_session_factory() as session:
            db = Database(session)
            role = await db.user.get_role(user_id=message.from_user.id)
            return role == Role.supervisor


class BaristaFilter(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message, bot: Bot) -> bool:
        async with async_session_factory() as session:
            db = Database(session)
            user = await db.user.get_one(user_id=message.from_user.id)
            return user.position == 'Бариста'


class WaiterFilter(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message, bot: Bot) -> bool:
        async with async_session_factory() as session:
            db = Database(session)
            user = await db.user.get_one(user_id=message.from_user.id)
            return user.position == 'Официант'


class AdministratorFilter(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message, bot: Bot) -> bool:
        async with async_session_factory() as session:
            db = Database(session)
            user = await db.user.get_one(user_id=message.from_user.id)
            return user.position == 'Администратор'
