import logging
import os
import re

import aiofiles
import aiohttp
import pytils

from aiogram import Router, F
from aiogram.filters import StateFilter, and_f, Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (Message, FSInputFile, CallbackQuery)
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramNotFound
from aiogram.utils.chat_action import ChatActionSender

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale

from core.bot import bot
from database import Database
from filters.filters import ChatTypeFilter, AdminFilter
from structures.keybords.keybords import (
    boss_main_menu,
    boss_payments_menu,
    points_menu_all,
    boss_category_menu,
    boss_home_works_menu,
    boss_home_expenses_menu,
    boss_payments_category_menu,
    boss_projects_works_menu,
    boss_projects_expenses_menu,
    cancel_menu,
    remove,
    no_check
)

from structures.fsm.expenses import (
    Home, Payments, Projects
)

from structures.keybords.keybords_list import boss_category_m
from services.async_google_service import google_add_row, google_authorize_token, google_save_file
from services.path import create_dir, clear_dir, create_src
from structures.role import Role
from utils.utils import includes_number, get_current_datetime
from core.config import settings, GoogleSheetsSettings

gs: GoogleSheetsSettings = settings.gs

router = Router(name=__name__)
router.message.filter(and_f(AdminFilter(), ChatTypeFilter(['private'])))

statesExpenses = StateFilter(
    Home(),
    Payments(),
    Projects(),
)


@router.message(Command("cancel"), statesExpenses)
@router.message(F.text.lower().in_({'отмена', 'отменить', '❌ отмена', '⬆ выйти', 'cancel'}), statesExpenses)
async def cancel_expenses_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    answer_text, reply_markup = ('Еще вопросы? 👇', boss_payments_menu)
    await message.answer(answer_text, disable_web_page_preview=True, reply_markup=reply_markup)


@router.message(StateFilter(None), F.text.lower() == '🏠 расход')
async def home_start(message: Message, state: FSMContext):
    """Добавление расходов на строительство дома старт"""
    await state.set_state(Home.category)
    await message.answer('Выбери категорию 👇', reply_markup=boss_category_menu)


@router.message(StateFilter(Home.category), F.text)
async def home_category(message: Message, state: FSMContext):
    if message.text in boss_category_m:
        await state.update_data(category=message.text)
        await state.set_state(Home.type)

        if message.text == '🛠 Работы':
            await message.answer('Что добавляем? 👇', reply_markup=boss_home_works_menu)
        if message.text == '🧾 Расходы':
            await message.answer('Что добавляем? 👇', reply_markup=boss_home_expenses_menu)
    else:
        await message.answer('Выбери категорию 👇', reply_markup=boss_category_menu)


@router.message(StateFilter(Home.type), F.text)
async def home_type(message: Message, state: FSMContext):
    await state.update_data(type=message.text)
    await state.set_state(Home.amount)
    await message.answer('Введи сумму 👇', reply_markup=cancel_menu)


@router.message(StateFilter(Home.amount), F.text)
async def home_amount(message: Message, state: FSMContext):
    if includes_number(message.text):
        await state.update_data(amount=str(re.sub('[^0-9,]', '', message.text.replace('.', ','))))
        await state.set_state(Home.comment)
        await message.answer('Добавь комментарий 👇', reply_markup=cancel_menu)
    else:
        await state.set_state(Home.amount)
        await message.answer('Введи сумму 👇', reply_markup=cancel_menu)


@router.message(StateFilter(Home.comment), F.text)
async def home_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    data = await state.get_data()

    date_time = get_current_datetime()

    await google_add_row(
        gs.BOOK_HOME,
        gs.SHEET_HOME,
        array=[date_time.strftime('%d.%m.%Y %H:%M:%S'),
               data['category'].split()[1],
               data['type'],
               data['amount'],
               data['comment']],
    )

    msg = f'Добавлен расход 👍\n' \
          f'{"*" * 25}\n' \
          f'{data["category"]}\n' \
          f'{data["type"]}\n' \
          f'Сумма: {"{:,.2f}₽".format(float(data["amount"].replace(",", ".")))}\n' \
          f'#Дом'

    await message.answer(msg, reply_markup=boss_payments_menu)
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == '💸 кофейни')
async def payments_start(message: Message, state: FSMContext):
    """Добавление расхода на точку старт"""
    try:
        await bot.delete_message(message.from_user.id, message.message_id - 1)
    except TelegramNotFound:
        logging.warning(f'MessageNotFound: {message.from_user.id} {message.message_id - 1}')
        pass
    await state.set_state(Payments.date)
    await message.reply('За какой день расход?', reply_markup=await SimpleCalendar(
        locale=await get_user_locale(message.from_user)).start_calendar())


@router.callback_query(SimpleCalendarCallback.filter(), StateFilter(Payments.date))
async def payments_date(callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    """Проверка выбора даты"""

    await callback_query.answer()

    calendar = SimpleCalendar(
        locale=await get_user_locale(callback_query.from_user), show_alerts=True
    )

    selected, date = await calendar.process_selection(callback_query, data=callback_data)
    user_id = callback_query.from_user.id

    if selected:
        date = date.strftime('%Y-%m-%d')
        await state.update_data(date=date)
        await state.set_state(Payments.point)
        await callback_query.message.edit_text(f"{date}", reply_markup=None)
        await bot.send_message(user_id, 'Выбери точку 👇', reply_markup=await points_menu_all())
    else:
        await bot.delete_message(user_id, message_id=callback_query.message.message_id)
        await state.clear()
        await bot.send_message(user_id, 'Какие вопросы? 👇', reply_markup=boss_main_menu)


@router.message(StateFilter(Payments.point), F.text)
async def payments_point(message: Message, state: FSMContext, db: Database):
    if await db.point.get_one(name=message.text):
        await state.update_data(point=message.text)
        await state.set_state(Payments.category)
        await message.answer('Выбери категорию расхода 👇', reply_markup=boss_payments_category_menu)
    else:
        await message.answer('Похоже ты ошибся, выбери точку 👇', reply_markup=await points_menu_all())


@router.message(StateFilter(Payments.category), F.text)
async def payments_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(Payments.amount)
    await bot.send_message(message.from_user.id, 'Введи сумму оплаты 👇', reply_markup=cancel_menu)


@router.message(StateFilter(Payments.amount), F.text)
async def payments_amount(message: Message, state: FSMContext):
    if includes_number(message.text):
        await state.update_data(amount=str(re.sub(r'[^\d,]', '', message.text.replace('.', ','))))
        await state.set_state(Payments.comment)
        await message.answer('Добавь комментарий к списанию 👇')
    else:
        await bot.send_message(message.from_user.id, 'Введи сумму оплаты 👇', reply_markup=cancel_menu)


@router.message(StateFilter(Payments.comment), F.text)
async def payments_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await state.set_state(Payments.file)
    await message.answer('Добавь фото чека 👇', reply_markup=no_check)


@router.message(StateFilter(Payments.file), F.photo | F.text)
async def payments_check(message: Message, state: FSMContext, db: Database):
    date_time = get_current_datetime()

    user_id = message.from_user.id
    user = await db.user.get_one(user_id=user_id)

    data = await state.get_data()

    if message.text == 'Без чека':
        await google_add_row(
            gs.BOOK_PAYMENTS,
            gs.SHEET_PAYMENTS,
            array=[date_time.strftime('%d.%m.%Y %H:%M:%S'),
                   data['date'],
                   user.full_name,
                   data['point'],
                   'Расход',
                   data['category'],
                   data['amount'],
                   data['comment'],
                   'Без чека'
                   ],
        )
    elif message.photo:

        create_dir(user_id)
        file_info = await bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        src = create_src(user_id, file_info.file_path)

        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file.getvalue())

        name = f'{data["point"]}_{date_time.strftime("%d_%m_%y %H_%M_%S")}_{data["category"]}_{data["amount"]}'
        file_id = await google_save_file(name=name, file_path=src)

        await google_add_row(
            gs.BOOK_PAYMENTS,
            gs.SHEET_PAYMENTS,
            array=[date_time.strftime('%d.%m.%Y %H:%M:%S'),
                   data['date'],
                   user.full_name,
                   data['point'],
                   'Расход',
                   data['category'],
                   data['amount'],
                   data['comment'],
                   f'https://drive.google.com/file/d/{file_id}/view?usp=drivesdk',
                   ],
        )
        clear_dir(user_id)
    else:
        await message.answer('Добавь фото чека 👇', reply_markup=no_check)

    msg = f'Добавлен расход 👍\n' \
          f'{"*" * 25}\n' \
          f'Точка: <b>{data["point"]}</b>\n' \
          f'Категория: {data["category"]}\n' \
          f'Сумма: {"{:,.2f}₽".format(float(data["amount"].replace(",", ".")))}\n' \
          f'#Расход'

    user_role_reply_markup = {
        Role.admin: boss_payments_menu,
        Role.staff: remove,
        Role.supervisor: remove
    }

    user_id = message.from_user.id
    user_role = await db.user.get_role(user_id=user_id)
    reply_markup = user_role_reply_markup.get(user_role)
    await message.answer(msg, reply_markup=reply_markup)
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == '🏬 проекты')
async def projects_start(message: Message, state: FSMContext):
    """Добавление расхода на проекты старт"""
    await state.set_state(Projects.point)
    await message.answer('Выбери точку 👇', reply_markup=await points_menu_all())


@router.message(StateFilter(Projects.point), F.text)
async def projects_point(message: Message, state: FSMContext, db: Database):
    if await db.point.get_one(name=message.text):
        await state.update_data(point=message.text)
        await state.set_state(Projects.category)
        await message.answer('Выбери категорию 👇', reply_markup=boss_category_menu)
    else:
        await message.answer('Похоже ты ошибся, выбери точку 👇', reply_markup=await points_menu_all())


@router.message(StateFilter(Projects.category), F.text)
async def projects_category(message: Message, state: FSMContext):
    if message.text in boss_category_m:
        await state.update_data(category=message.text)
        await state.set_state(Projects.type)

        if message.text == '🛠 Работы':
            await message.answer('Что добавляем? 👇', reply_markup=boss_projects_works_menu)
        if message.text == '🧾 Расходы':
            await message.answer('Что добавляем? 👇', reply_markup=boss_projects_expenses_menu)
    else:
        await message.answer('Выбери категорию 👇', reply_markup=boss_category_menu)


@router.message(StateFilter(Projects.type), F.text)
async def projects_type(message: Message, state: FSMContext):
    await state.update_data(type=message.text)
    await state.set_state(Projects.amount)
    await message.answer('Введи сумму 👇', reply_markup=cancel_menu)


@router.message(StateFilter(Projects.amount), F.text)
async def projects_amount(message: Message, state: FSMContext):
    if includes_number(message.text):
        await state.update_data(amount=str(re.sub(r'[^\d,]', '', message.text.replace('.', ','))))
        await state.set_state(Projects.comment)
        await message.answer('Добавь комментарий 👇', reply_markup=cancel_menu)
    else:
        await message.answer('Введи сумму 👇', reply_markup=cancel_menu)


@router.message(StateFilter(Projects.comment), F.text)
async def projects_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)

    data = await state.get_data()

    # if p['category'] == '🛠 Работы':
    date_time = get_current_datetime()
    await google_add_row(
        gs.BOOK_HOME,
        gs.SHEET_PROJECTS,
        array=[date_time.strftime('%d.%m.%Y %H:%M:%S'),
               data['point'],
               data['category'].split()[1],
               data['type'],
               data['amount'],
               data['comment']],
    )

    msg = f'Добавлен расход 👍\n' \
          f'{"*" * 25}\n' \
          f'{data["category"]}\n' \
          f'{data["type"]}\n' \
          f'Сумма: {"{:,.2f}₽".format(float(data["amount"].replace(",", ".")))}\n' \
          f'#Проекты'

    await message.answer(msg, reply_markup=boss_main_menu)
    await state.clear()
    # elif p['category'] == '🧾 Расходы':
    #     await message.answer('Добавь фото чека 👇', reply_markup=no_check)


# async def projects_check(message: Message, state: FSMContext):
#     date_time = get_current_datetime()
#     async with state.proxy() as p:
#
#         msg = f'Добавлен расход 👍\n' \
#               f'{"*" * 25}\n' \
#               f'{p["category"]}\n' \
#               f'{p["type"]}\n' \
#               f'Сумма: {"{:,.2f}₽".format(float(p["amount"].replace(",", ".")))}\n' \
#               f'#Проекты'
#
#         if message.text == 'Без чека':
#             await google_add_row(g.BOOK_HOME, g.SHEET_PROJECTS,
#                                  [date_time.strftime('%d.%m.%Y %H:%M:%S'),
#                                   p['point'],
#                                   p['category'].split()[1],
#                                   p['type'],
#                                   p['amount'],
#                                   p['comment']])
#
#             await message.answer(msg, reply_markup=boss_payments_menu)
#             await state.finish()
#
#         elif not message.media_group_id and message.photo:
#             if await file_size_check(message):
#                 await Projects.file.set()
#             else:
#                 p['file'] = message.photo[2].file_id
#                 create_dir(message.from_user.id)
#                 file_info = await bot.get_file(message.photo[len(message.photo) - 1].file_id)
#                 downloaded_file = await bot.download_file(file_info.file_path)
#                 src = create_src(message.from_user.id, file_info.file_path)
#
#                 with open(src, 'wb') as new_file:
#                     new_file.write(downloaded_file.getvalue())
#
#                 name = f'Чек {date_time.strftime("%d_%m_%y %H_%M_%S")} {p["type"].lower()} {p["amount"]}'
#                 file_id = await google_save_file(name=name, file_path=src)
#
#                 await google_add_row(g.BOOK_HOME, g.SHEET_PROJECTS,
#                                      [date_time.strftime('%d.%m.%Y %H:%M:%S'),
#                                       p['point'],
#                                       p['category'].split()[1],
#                                       p['type'],
#                                       p['amount'],
#                                       p['comment'],
#                                       f'https://drive.google.com/file/d/{file_id}/view?usp=drivesdk'])
#                 clear_dir(message.from_user.id)
#
#                 await message.answer(msg, reply_markup=boss_payments_menu)
#                 await state.finish()
#         else:
#             await message.answer('Добавь фото чека 👇', reply_markup=no_check)


@router.message(F.text.lower() == '🏠 отчет дом')
async def construction_pdf_report(message: Message):
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        url = (
            f"https://docs.google.com/spreadsheets/d/{gs.BOOK_HOME}/export?format=pdf&gid={gs.HOME_SHEET_ID}"
            f"&size=A4&portrait=false")

        # Ваши учётные данные
        headers = {
            "Authorization":
                f"Bearer {await google_authorize_token()}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as res:
                content = await res.read()
                create_dir(dir_type='report')
                file_path = f'{os.getcwd()}/src/reports/construction.pdf'
                async with aiofiles.open(file=file_path, mode='wb') as file:
                    await file.write(content)

        now = pytils.dt.ru_strftime(u'%d.%m.%y', inflected=True, date=get_current_datetime())
        await message.answer_document(FSInputFile(file_path, filename=f'Отчет по стройке {now}.pdf'),
                                      caption=f'Отчет по стройке {now}',
                                      reply_markup=boss_payments_menu)
        clear_dir(dir_type='report')


@router.message(F.text.lower() == '🏬 отчет проект')
async def project_pdf_report(message: Message):
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        url = (
            f"https://docs.google.com/spreadsheets/d/{gs.BOOK_HOME}/export?format=pdf&gid={gs.PROJECTS_SHEET_ID}"
            f"&size=A4&portrait=false")

        # Ваши учётные данные
        headers = {
            "Authorization":
                f"Bearer {await google_authorize_token()}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as res:
                content = await res.read()
                create_dir(dir_type='report')
                file_path = f'{os.getcwd()}/src/reports/projects.pdf'
                async with aiofiles.open(file=file_path, mode='wb') as file:
                    await file.write(content)

        now = pytils.dt.ru_strftime(u'%d.%m.%y', inflected=True, date=get_current_datetime())
        await message.answer_document(FSInputFile(file_path, filename=f'Отчет по проекту {now}.pdf'),
                                      caption=f'Отчет по проекту {now}',
                                      reply_markup=boss_payments_menu)
        clear_dir(dir_type='report')
