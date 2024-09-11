import asyncio
import contextlib
import logging
import warnings

from aiogram import Bot
from aiogram.types import BotCommandScopeChat

from cache import Cache
from dispatcher import get_dispatcher, get_redis_storage

# from aiogram.fsm.storage.redis import RedisStorage
# from aioredis import Redis
# from redis.asyncio.client import Redis

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler_di import ContextSchedulerDecorator

from core.config import settings
from core.bot import bot

from database import create_db, async_session_factory

from commands.commands import commands_admin
from hendlers.mailings import mailing

from structures.mw_data_structure import TransferData

from services.logging_configurate import logging_configurate

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pytils")

ALLOWED_UPDATES = ["message", "callback_query"]

# storage = get_redis_storage(
#     redis=Redis(
#         host=settings.redis.REDIS_HOST or '127.0.0.1',
#         password=settings.redis.REDIS_USER_PASSWORD or None,
#         username=settings.redis.REDIS_USER or None,
#         port=settings.redis.REDIS_PORT or 6380,
#         db=settings.redis.REDIS_DATABASE or 0,
#     )
# )

"""
https://habr.com/ru/articles/725086/
https://docs.aiogram.dev/en/latest/utils/keyboard.html#reply-keyboard
https://www.youtube.com/watch?v=55w2QpPGC-E&list=PLNi5HdK6QEmWLtb8gh8pwcFUJCAabqZh_&index=6
https://docs.google.com/spreadsheets/d/1L7CbxCwtRB79VmpqbV7R2PyE3vcy8IZIlq6IGDlH04w/edit?gid=0#gid=0
https://github.com/o-murphy/aiogram3_calendar/tree/master
https://github.com/mahenzon/micro-shop/blob/1d5b9820e2185786599748047bd64fe232079e7c/crud.py
https://www.youtube.com/watch?v=uLp-zgset00
https://github.com/artemonsh/sqlalchemy_course/blob/main/src/queries/orm.py
https://github.com/artemonsh/sqlalchemy_course/blob/main/src/queries/orm.py
https://github.com/mahenzon/demo-tg-bot/blob/e4b687d51600722f1f93b26fdc17d329bad06ee1/routers/common.py
"""


async def on_startup(bot):
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=commands_admin, scope=BotCommandScopeChat(chat_id=settings.bot.MASTER))

    # await drop_db()
    await create_db()

    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

    if settings.use_redis:
        job_stores = {
            'default': RedisJobStore(
                jobs_key='dispatched_trips_jobs',
                run_times_key='dispatched_trips_running',
                host=settings.redis.REDIS_HOST or '127.0.0.1',
                port=settings.redis.REDIS_PORT or 6380,
                db=2,
            )
        }

        scheduler = ContextSchedulerDecorator(
            AsyncIOScheduler(timezone='Europe/Moscow', jobstores=job_stores))
        scheduler.ctx.add_instance(bot, declared_class=Bot)

    scheduler.add_job(mailing.write_off_coffee, trigger='cron', day_of_week='mon', hour=8)
    scheduler.add_job(mailing.send_reminder_order, trigger='cron', day_of_week='mon', hour=10)
    scheduler.add_job(mailing.send_reminder_order, trigger='cron', day_of_week='tue', hour=10)
    scheduler.add_job(mailing.send_reminder_order, trigger='cron', day_of_week='sun', hour=9, minute=30)
    scheduler.add_job(mailing.send_reminder_coffee_machine, trigger='cron', day_of_week='mon', hour=10)
    scheduler.add_job(mailing.send_reminder_coffee_machine, trigger='cron', day_of_week='mon', hour=21)
    scheduler.add_job(mailing.revenue_by_day, trigger='cron', hour=0, minute=30, kwargs={'user_id': None})
    # scheduler.add_job(mailing.not_send_evening_reports, trigger='cron', hour=3)
    scheduler.add_job(mailing.safe, trigger='cron', hour=9)
    scheduler.add_job(mailing.send_check_up, trigger='cron', hour=10)
    # scheduler.add_job(mailing.not_send_morning_reports, trigger='cron', hour=13)
    scheduler.add_job(mailing.send_check_up, trigger='cron', hour=21)
    scheduler.add_job(mailing.send_comes_out, trigger='cron', hour=22)

    # scheduler.add_job(mailing.update_supervisor_check_report, trigger='interval', hours=1)
    scheduler.start()


async def on_shutdown():
    ...
    # logging.error(f"'{await bot.get_me().first_name}' stopped")


async def main() -> None:
    logging_configurate(logging.INFO)

    cache = Cache()

    # storage = get_redis_storage(redis=cache.redis_client)
    dp = get_dispatcher(storage=get_redis_storage(redis=cache.redis_client)) if settings.use_redis else get_dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),  # allowed_updates=ALLOWED_UPDATES
            **TransferData(pool=async_session_factory, cache=cache),
        )
    except Exception as ex:
        logging.error("[POLLING ERROR]: %r", ex)
    finally:
        await bot.session.close()
        await dp.storage.close()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt, SystemExit):
        asyncio.run(main(), debug=True)
