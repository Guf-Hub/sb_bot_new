import logging
from datetime import datetime, timedelta
import calendar

from aiogram import Router, F
from aiogram.filters import Command, and_f, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from filters.filters import AdminFilter, ChatTypeFilter

from structures.keybords import (
    boss_report_menu,
    boss_other_menu,
    cancel_menu
)


from core.bot import bot
from database import Database
from utils.utils import get_current_datetime, dt_formatted, seconds_to_time
from core.config import settings, GoogleSheetsSettings


gs: GoogleSheetsSettings = settings.gs

router = Router(name=__name__)
router.message.filter(and_f(AdminFilter(), ChatTypeFilter(['private'])))


@router.message(F.text.lower().in_({'📈 за сегодня'}))
async def report_by_day(message: Message, db: Database):
    """Отчет по отправленным за день"""
    date = dt_formatted(6)

    reports = await db.check_cafe.get_reports_by_period(date, date)
    supervisors = await db.user.get_supervisors()
    point_count = dict(zip([sv.user_id for sv in supervisors], [len(sv.points.split(", ")) for sv in supervisors]))

    print(list(reports))
    print(list(supervisors))
    print(point_count)
    res = []
    for report in reports:
        ...
    #
    #     i = (report.point, report.type, report.in_time, report.out_time, report.time)
    #     x = f'Ср. время: {(seconds_to_time(i[4]))} ч.\n' if i[4] is not None else ''
    #     y = f'Норматив: {point_count[i[0]]} шт.\n' if i[0] in point_count else ''
    #     res.append(f'{i[0]}\n'
    #                f'Тип: {i[1]}\n'
    #                f'{x}'
    #                f'{y}'
    #                f'Получено: {i[2]} шт.\n'
    #                f'Вовремя: {i[3]} шт.\n'
    #                f'{round(i[3] / i[2] * 100.0, 1)} %')
    #
    # if len(res):
    #     await message.answer(f'\n{"*" * 15}\n'.join(res), allow_sending_without_reply=True,
    #                          reply_markup=boss_report_menu)
    # else:
    #     await message.answer(f'Нет данных 🤷‍♂', allow_sending_without_reply=True,
    #                          reply_markup=boss_report_menu)


@router.message(F.text.lower().in_({'📈 за месяц'}))
async def report_by_month(message: Message, db: Database):
    """Отчет по отправленным за месяц"""
    date = get_current_datetime()
    start_date = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
    end_date = (datetime(date.year, date.month, 1) + timedelta(
        days=calendar.monthrange(date.year, date.month)[1] - 1)).strftime("%Y-%m-%d")

    reports = await db.check_cafe.get_reports_by_period(start_date, end_date)

    now = message.date
    supervisors = await db.user.get_supervisors()
    point_count = dict(zip([sv.user_id for sv in supervisors], [len(sv.points.split(", ")) for sv in supervisors]))

    print(list(reports))
    print(list(supervisors))
    print(point_count)

    res = []
    for i in reports:
        x = f'Ср. время: {seconds_to_time(i[4])} ч.\n' if i[4] is not None else ''
        y = int(point_count[i[0]]) if i[0] in point_count else ''
        res.append(f'{i[0]}\n'
                   f'Тип: {i[1]}\n'
                   f'{x}'
                   f'Норматив: {calendar.monthrange(now.year, now.month)[1] * y} шт.\n'
                   f'Получено: {i[2]} шт.\n'
                   f'Вовремя: {i[3]} шт.\n'
                   f'{round(i[3] / i[2] * 100.0, 1)} %')

    if len(res):
        await message.answer(f'\n{"*" * 15}\n'.join(res), allow_sending_without_reply=True,
                             reply_markup=boss_report_menu)
    else:
        await message.answer(f'Нет данных 🤷‍♂', allow_sending_without_reply=True, reply_markup=boss_report_menu)


# async def update_checks(message: Message):
#     """Обновить список отчетов в книге супервайзера"""
#     await update_supervisor_check_report()
#     await message.answer('Обновили данные в Книге супервайзера 👍', reply_markup=boss_other_menu)
#



# @dp.callback_query_handler(Text(contains=['checkRotation']))
# async def check_report_start(query: CallbackQuery):
#     """Стар подтверждения отчета callback Text(contains=['check_rotation'])"""
#     try:
#         await dp.throttle('vote', rate=1)
#     except Throttled:
#         return await query.answer('Слишком много запросов...')
#
#     user_id = query.from_user.id
#     if user_id in set(x[0] for x in db.get_active()):
#         answer_data = query.data
#         point = answer_data.split(' ')[1]
#         await query.message.edit_text(text='Красава!', reply_markup=None)
#
#         sv_id = None
#         supervisors = db.get_supervisors()
#         for sv in supervisors:
#             try:
#                 sv_id = sv[0]
#                 if sv[1] and point in sv[1].split(', '):
#                     await bot.send_message(sv_id, f'{point} - ротация соблюдена', reply_markup=main_menu)
#             except Exception as e:
#                 logging.warning(f'{sv_id} > {e}')
#                 continue
#     else:
#         await bot.delete_message(user_id, message_id=query.message.message_id)
#         await bot.send_message(user_id, 'Нет доступа', reply_markup=remove)


#     d.register_message_handler(report_by_day, Text(equals='📈 за сегодня', ignore_case=True))
#     d.register_message_handler(report_by_month, Text(equals='📈 за месяц', ignore_case=True))
