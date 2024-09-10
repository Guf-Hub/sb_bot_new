"""This file contains build dispatcher logic."""
import os

from aiogram import Dispatcher
from aiogram.fsm.storage.base import BaseEventIsolation, BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.strategy import FSMStrategy

from redis.asyncio.client import Redis

from database.db import async_session_factory

from hendlers import router
from middelewares import (
    DataBaseSession,
    RestrictionsMiddleware,
    RoleMiddleware,
    SchedulerMiddleware,
    # ThrottlingMiddleware,
    ThrottlingSimpleMiddleware,
)

from core.config import settings
from cache import Cache
from middelewares.db import DatabaseMiddleware


def get_redis_storage(
        redis: Cache, state_ttl=settings.redis.REDIS_TTL_STATE, data_ttl=settings.redis.REDIS_TTL_DATA
):
    if settings.use_redis:
        return RedisStorage(redis=redis, state_ttl=state_ttl, data_ttl=data_ttl)


# def get_redis_redis_storage(
#         redis: Redis, state_ttl=settings.redis.REDIS_TTL_STATE, data_ttl=settings.redis.REDIS_TTL_DATA
# ):
#     """This function create redis storage or get it forcely from configuration.
#
#     :param redis: Redis client instance
#     :param state_ttl: FSM State Time-To-Delete timer in seconds (has effect only
#     for Redis database)
#     :param data_ttl: FSM Data Time-To-Delete timer in seconds (has effect only
#     for Redis database)
#     :return: Created Redis storage.
#     """
#     return RedisStorage(redis=redis, state_ttl=state_ttl, data_ttl=data_ttl)


def get_dispatcher(
        storage: BaseStorage = MemoryStorage(),
        fsm_strategy: FSMStrategy | None = FSMStrategy.CHAT,
        event_isolation: BaseEventIsolation | None = None,
) -> Dispatcher:
    """This function set up dispatcher with routers, filters and middlewares."""
    dp = Dispatcher(
        storage=storage,
        fsm_strategy=fsm_strategy,
        events_isolation=event_isolation,
    )

    dp.include_router(router)

    # Register middlewares
    # dp.update.middleware(DataBaseSession(session_pool=async_session_factory))
    dp.update.middleware(DatabaseMiddleware())
    # dp.message.middleware(RoleMiddleware())
    # dp.update.middleware(SchedulerMiddleware(scheduler))
    dp.message.middleware(RestrictionsMiddleware())
    # dp.message.middleware.register(ThrottlingMiddleware(storage=storage))
    dp.message.middleware.register(ThrottlingSimpleMiddleware(throttle_time_spin=2, throttle_time_other=1))

    return dp
