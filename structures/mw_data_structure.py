"""
This file contains TypedDict structure to store data which will
transfer throw Dispatcher->Middlewares->Handlers
"""
from typing import Callable, TypedDict

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from database import Database

from cache import Cache
from .role import Role


class TransferData(TypedDict):
    pool: Callable[[], AsyncSession]
    session: AsyncSession | None
    db: Database | None
    cache: Cache | None
    bot: Bot


class TransferUserData(TypedDict):
    role: Role
