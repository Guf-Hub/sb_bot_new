#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from typing import Union

import pytils
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy.ext.asyncio import AsyncSession

from core.bot import bot
from core.config import settings, TgBot, GoogleSheetsSettings
from database import async_engine, db, WriteOff, Database

from structures.keybords import boss_main_menu, get_points
from structures.keybords.cb_makers import create_inline_kb, create_inline_url_kb

from services.google_service import (google_exit, google_revenue, google_add_row, google_safe)
from services.async_google_service import google_safe, google_revenue, google_exits
from common.questions import sheets
from utils.utils import get_current_datetime, dt_formatted

tg: TgBot = settings.bot
gs: GoogleSheetsSettings = settings.gs


async def send_reminder_order():
    """Рассылка заказ кофе и десертов"""

    curr_datetime = get_current_datetime()
    tomorrow = pytils.dt.ru_strftime(u'%d.%m.%y', inflected=True, date=curr_datetime + timedelta(days=1))
    weekday = pytils.dt.ru_strftime(u'%A', inflected=True, date=curr_datetime)
    now = pytils.dt.ru_strftime(u'%d.%m.%y', inflected=True, date=curr_datetime)

    async with AsyncSession(async_engine) as session:
        users = await db.users_active_get(session)

    for user in users:
        position = user.position
        point = user.point
        name = user.full_name
        user_id = user.user_id

        inline_order = create_inline_url_kb(btns={'Перейти в заказ': 'https://clck.ru/Vrxcr'})
        inline_rotation = create_inline_kb(btns={'Проверил! Ротация соблюдена': f'checkRotation_{point}'})

        try:
            if position in ['Ст. бариста', 'Супервайзер', 'Бариста']:
                if weekday == 'воскресенье':
                    await bot.send_message(
                        chat_id=user_id,
                        text=f'<strong>{name}</strong>, привет!\n\n'
                             f'Если ты в смене, проверь дату изготовления следующих позиций:\n'
                             f'🔸 кофе;\n'
                             f'🔸 молоко обычное;\n'
                             f'🔸 молоко безлактозное;\n'
                             f'🔸 молоко банановое;\n'
                             f'🔸 молоко кокосовое;\n'
                             f'🔸 молоко миндальное.\n\n'
                             f'<i>При наличии, нескольких шт. товаров одного вида из перечисленных, '
                             f'товар с подходящим сроком годности помести вперёд!</i>',
                        reply_markup=inline_rotation
                    )
                if weekday == 'понедельник':
                    await bot.send_message(
                        user_id,
                        f'<strong>{name}</strong>, привет!\n'
                        f'Завтра <strong>{tomorrow} до 12:00</strong>, отправь заказ.\n'
                        f'Поставщик: Мастер РТК\nСумма заказа от 5000 руб.',
                        reply_markup=inline_order
                    )
                if weekday == 'вторник':
                    await bot.send_message(
                        user_id,
                        f'<strong>{name}</strong>, привет!\n'
                        f'Сегодня <strong>{now} до 12:00</strong>, отправь заказ.\n'
                        f'Поставщик: Мастер РТК\nСумма заказа от 5000 руб.',
                        reply_markup=inline_order
                    )
                if weekday == 'понедельник' and point != 'Балашиха':
                    await bot.send_message(
                        user_id,
                        f'<strong>{name}</strong>, привет!\n'
                        f'Завтра <strong>{tomorrow} до 16:00</strong>, отправь заказ.\n'
                        f'Поставщик: Десерт фентези\n'
                        f'Сумма заказа от 5000 руб.',
                        reply_markup=inline_order
                    )
                if weekday == 'вторник' and point != 'Балашиха':
                    await bot.send_message(
                        user_id,
                        f'<strong>{name}</strong>, привет!\n'
                        f'Сегодня <strong>{now} до 16:00</strong>, отправь заказ.\n'
                        f'Поставщик: Десерт фентези\n'
                        f'Сумма заказа от 5000 руб.',
                        reply_markup=inline_order
                    )

                logging.info('Send reminder order: %s, %s %s > OK', user_id, name,
                             curr_datetime.strftime("%d.%m.%Y %H:%M:%S"))
        except Exception as ex:
            logging.warning('Send reminder order: %s, %s ошибка рассылки > %s', user_id, name, ex)
            continue

    logging.info('Send reminder order: %s > OK', curr_datetime)


# TODO оживить
# async def not_send_morning_reports():
#     """Проверка, кто прислал утренний отчёт"""
#     curr_datetime = get_current_datetime()
#     data = db.get_data_report(date=dt_formatted(6))
#     morning_10 = []
#     morning_12 = []
#     if not data:
#         for boss_id in tg.BOSS:
#             try:
#                 msg = f'<b>INFO {pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=curr_datetime)}</b>\n' \
#                       f'☀ Утренний отчёт\n' \
#                       f'{"*" * 25}\n' \
#                       f'Нет отчётов'
#
#                 await bot.send_message(boss_id, msg)
#             except Exception as e:
#                 logging.warning(f'{boss_id} > {e}')
#     else:
#         points = get_points()
#         for i in data:
#             report_type = i[3]
#             point = i[6]
#
#             if point in points:
#                 if report_type == 'Утренний до 10':
#                     morning_10.append(point)
#                 elif report_type == 'Утренний до 12':
#                     morning_12.append(point)
#
#         morning_10 = set(morning_10)
#         morning_12 = set(morning_12)
#         x_10 = set(points) - set(morning_10)
#         x_12 = set(points) - set(morning_12)
#
#         for boss_id in tg.BOSS:
#             if boss_id != tg.BOSS_ONLY and boss_id != tg.MASTER:
#                 try:
#                     result_10 = f'Все прислали 👍' if len(morning_10) == len(
#                         points) else f'Прислали: {", ".join(sorted(morning_10))}\nНе прислали: {", ".join(sorted(x_10))}'
#
#                     msg_10 = f'<b>INFO {pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=curr_datetime)}</b>\n' \
#                              f'☀ Утренний (до 10)\n' \
#                              f'{"*" * 25}\n' \
#                              f'{result_10}'
#
#                     await bot.send_message(boss_id, msg_10)
#
#                     result_12 = f'Все прислали 👍' if len(morning_12) == len(
#                         points) else f'Прислали: {", ".join(sorted(morning_12))}\nНе прислали: {", ".join(sorted(x_12))}'
#
#                     msg_12 = f'<b>INFO {pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=curr_datetime)}</b>\n' \
#                              f'☀ Утренний (до 12)\n' \
#                              f'{"*" * 25}\n' \
#                              f'{result_12}'
#                     await bot.send_message(boss_id, msg_12)
#                 except Exception as e:
#                     logging.warning(f'{boss_id} ошибка рассылки > {e}')
#                     continue
#     logging.info(f'not_send_morning_reports {dt_formatted()} > OK')
#
# TODO оживить
# async def not_send_evening_reports():
#     """Проверка, кто прислал вечерний отчёт"""
#     curr_datetime = get_current_datetime(days=-1)
#     data = db.get_data_report(date=dt_formatted(6, minus_days=1))
#     evening = []
#     if not data:
#         for boss_id in tg.BOSS:
#             try:
#                 msg = f'<b>INFO {pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=curr_datetime)}</b>\n' \
#                       f'🌘 Вечерний отчёт\n' \
#                       f'{"*" * 25}\n' \
#                       f'Нет отчётов'
#
#                 await bot.send_message(boss_id, msg)
#             except Exception as e:
#                 logging.warning(f'{boss_id} > {e}')
#     else:
#         points = get_points()
#         for i in data:
#             report_type = i[3]
#             point = i[6]
#
#             if point in points and report_type == 'Вечерний':
#                 evening.append(point)
#
#         evening = set(evening)
#         y = set(points) - set(evening)
#
#         for boss_id in tg.BOSS:
#             if boss_id != tg.BOSS_ONLY and boss_id != tg.MASTER:
#                 try:
#                     result = f'Все прислали 👍' if len(evening) == len(
#                         points) else f'Прислали: {", ".join(sorted(evening))}\nНе прислали: {", ".join(sorted(y))}'
#
#                     msg = f'<b>INFO {pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=curr_datetime)}</b>\n' \
#                           f'🌘 Вечерний отчёт\n' \
#                           f'{"*" * 25}\n' \
#                           f'{result}'
#
#                     await bot.send_message(boss_id, msg)
#                 except Exception as e:
#                     logging.warning(f'{boss_id} ошибка рассылки > {e}')
#                     continue
#     logging.info(f'not_send_evening_reports {dt_formatted()} > OK')


async def revenue_by_day(user_id: Union[str, int] = None):
    """Отправка выручки за день в 00:05"""

    date = pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=get_current_datetime(days=-1))
    revenue = await google_revenue()  # await google_revenue(gs.BOOK_SALARY, gs.SHEET_SALARY)

    msg = f'<b>INFO {date}</b>\n' \
          f'💰 Выручка за день\n' \
          f'{"*" * 25}\n' \
          f'{revenue}\n' \
          f'#Выручка'

    if user_id:
        await bot.send_message(user_id, msg)
    else:
        for user_id in tg.BOSS:
            try:
                await bot.send_message(user_id, msg, reply_markup=boss_main_menu)
            except Exception as ex:
                logging.warning('Revenue by day: %s ошибка рассылки > %s', user_id, ex)
                continue

    logging.info('Revenue by day: %s > OK', dt_formatted())


async def safe():
    """Отправка остатка в сейфе в 9:00 тем кто в смене"""
    curr_datetime = get_current_datetime()
    data = await google_safe()  # await google_safe(gs.BOOK_SALARY, gs.SHEET_SAFE)

    async with AsyncSession(async_engine) as session:
        users = await db.users_active_get(session)

    schedule_today = await google_exits(offset=0, scheduled=True)

    if schedule_today:
        check = []
        for user in users:
            user_id = user.user_id
            last_name = user.last_name
            point = user.point
            try:
                if last_name in schedule_today and user_id not in check and user_id not in tg.BOSS:
                    d = '\n'.join([f'{el[0]} {el[1]}' for el in data if el[0] == point and el[1] is not None])
                    msg = f'<b>INFO {pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=curr_datetime)}</b>\n' \
                          f'💰 Остаток в сейфе\n' \
                          f'{"*" * 25}\n' \
                          f'{d}\n' \
                          f'#Сейф'
                    logging.info(f'safe: {last_name} > {msg}')
                    check.append(user_id)
                    await bot.send_message(user_id, msg)
            except Exception as ex:
                logging.warning('Safe: %s %s ошибка рассылки > %s', user_id, user.full_name, ex)
                continue

        logging.info('Safe: %s > OK', dt_formatted())
    else:
        logging.warning('Safe: %s', curr_datetime)


async def safe_boss(user_id: Union[str, int] = None, reply_markup=boss_main_menu):
    """Отправка остатка в сейфе"""

    curr_datetime = get_current_datetime()
    values = await google_safe(boss=True)  # await google_safe(gs.BOOK_SALARY, gs.SHEET_SAFE, boss=True)

    if values:
        msg = f'<b>INFO {pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=curr_datetime)}</b>\n' \
              f'💰 Остаток в сейфе\n' \
              f'{"*" * 25}\n' \
              f'{values}\n' \
              f'#СейфОстатки'
    else:
        msg = 'Нет данных'

    await bot.send_message(chat_id=user_id, text=msg, reply_markup=reply_markup)
    logging.info('Safe boss: %s > OK', dt_formatted())


async def send_comes_out():
    """`Выход завтра` напоминание"""
    curr_datetime = get_current_datetime()

    async with AsyncSession(async_engine) as session:
        users = await db.users_active_get(session)

    schedule_tomorrow = await google_exits(offset=1, scheduled=True)
    # await exit_google(gs.BOOK_TABLE_ID, gs.SHEET_EXITS, period=2, staff_array=True)
    if schedule_tomorrow:
        check = []
        for user in users:
            user_id = user.user_id
            last_name = user.last_name
            first_name = user.first_name
            point = user.point

            try:
                if last_name in schedule_tomorrow and user_id not in check and user_id not in tg.BOSS:
                    msg = f'<strong>{first_name}</strong>, привет!\nЗавтра на работу: {point}.\n' \
                          f'Если это не так, сообщи Александре @sasha_izy, она поправит график.'
                    check.append(user_id)
                    await bot.send_message(user_id, msg)
                    logging.info(f'comes_out: {last_name} > OK')
            except Exception as ex:
                logging.warning('Send comes out: %s %s ошибка рассылки > %s', user_id, user.full_name, ex)
                continue

        logging.info('Send comes out: %s > OK', dt_formatted())
    else:
        logging.warning("Send comes out: %s", curr_datetime)


async def send_check_up():
    """Напоминание заполнить `Чек UP`"""
    curr_datetime = get_current_datetime()

    async with AsyncSession(async_engine) as session:
        users = await db.users_active_get(session)

    schedule_today = await google_exits(offset=0, scheduled=True)
    # await exit_google(gs.BOOK_TABLE_ID, gs.SHEET_EXITS, period=1, staff_array=True)
    if schedule_today:
        check = []
        for user in users:
            user_id = user.user_id
            last_name = user.last_name
            first_name = user.first_name

            try:
                if last_name in schedule_today and user_id not in check:
                    time = dt_formatted(5)
                    check.append(user_id)

                    if time == '09':
                        await bot.send_message(user_id,
                                               f'<strong>${first_name}</strong>, сфотографируй настроенный эспрессо и '
                                               f'отправь фото с 9:50 до 10:00.\n'
                                               f'"До 10", фото по точке отправь до 10:00!'
                                               f'"До 12", видео по точке отправь до 12:00!')
                    elif time == '21':
                        await bot.send_message(user_id, f'<strong>${first_name}</strong>, смена подходит к концу.\n'
                                                        f'Не забудь отправить отчет по точке после закрытия, до 00:00!')
            except Exception as e:
                logging.warning(f'{user_id}, {user.full_name} ошибка рассылки > {e}')
                continue
        logging.info(f'send_check_up {curr_datetime} > OK')
    else:
        logging.warning(f'send_check_up {curr_datetime}')


async def write_off_coffee():
    """Списание кофе понедельник `Чистка кофемолки`"""
    curr_datetime = get_current_datetime()

    async with AsyncSession(async_engine) as session:
        points = await get_points()
        for point in points:
            user = await Database(session).user.get_one(user_id=6968474689)
            await Database(session).write_off.add(
                WriteOff(
                    point=point,
                    user_id=user.id,
                    code=4014,
                    quantity=0.006,
                    reason="Порча",
                    comment="Чистка кофемолки",
                )
            )

        await google_add_row(
            gs.BOOK_WRITE_OFF_ID, sheets[point],
            array=[
                curr_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                6968474689,
                "Bot сервисный",
                4014,
                "",
                0.006,
                "Порча",
                "Чистка кофемолки",
                "",
                "",
                "Списание без МОЛ"
            ]
        )

    logging.info(f'Write off coffee: %s > OK', curr_datetime)


async def send_reminder_coffee_machine():
    """Напоминание `Очистка кофемолки по понедельникам`"""
    curr_datetime = get_current_datetime()
    weekday = pytils.dt.ru_strftime(u'%A', inflected=True, date=curr_datetime)

    if weekday == "понедельник":

        async with AsyncSession(async_engine) as session:
            users = await db.users_active_get(session)

        now = pytils.dt.ru_strftime(u'%d.%m.%y', inflected=True, date=curr_datetime)
        schedule_today = await google_exits(offset=0, scheduled=True)

        if schedule_today:
            check = []
            for user in users:
                user_id = user.user_id
                last_name = user.last_name
                first_name = user.first_name

                try:
                    if last_name in schedule_today and user_id not in check:
                        time = dt_formatted(5)
                        check.append(user_id)
                        if time == '10':

                            inline = create_inline_url_kb(
                                btns={'Обучающее видео': 'https://clck.ru/gki6W'},
                            )

                            msg = f'<strong>{first_name}</strong>, привет!\n' \
                                  f'Сегодня {now} после смены нужно почистить кофемолку.\n' \
                                  f'Если не один в смене, распределите обязанности.'
                            await bot.send_message(user_id, msg, reply_markup=inline)
                        elif time == '21':
                            await bot.send_message(user_id, f'Уверен, ты не забыл почистить кофемолку.')
                except Exception as e:
                    logging.warning(f'{user_id}, {user.full_name} ошибка рассылки > {e}')
                    continue
        logging.info(f'send_reminder_coffee_machine {curr_datetime} > OK')
    else:
        logging.warning(f'send_reminder_coffee_machine {curr_datetime}')

# TODO оживить
# async def update_supervisor_report():
#     """Обновление данных в гугл таблице Книга SV (ежедневные отчеты лист DAY)"""
#     data = db.fetchall('check_day',
#                        ['report_id', 'add_date', 'add_datetime', 'check_datetime', 'duration', 'type', 'name', 'point',
#                         'question_one', 'verified', 'comment', 'in_time', 'supervisor'])
#     await google_worksheet_update(gs.BOOK_SUPERVISOR, gs.SHEET_DAY_CHECK, data)

# TODO оживить
# async def drop_records():
#     from datetime import datetime
#     # start_month = datetime(datetime.now().year, datetime.now().month, 1).strftime('%Y-%m-%d')
#     start_year = datetime(datetime.now().year, 1, 1).strftime('%Y-%m-%d')
#     db.delete('check_day', 'add_date', start_year, '<')
#     db.delete('write_off', 'add_date', start_year, '<')
#     logging.info(f'drop_records {dt_formatted()} > OK')
