#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import pprint
import random
from datetime import datetime, timedelta
import calendar
import pytils

from aiogram import Router, F
from aiogram.filters import Command, and_f, StateFilter
from aiogram.types import (Message, CallbackQuery)
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext

from database.models import Point
from filters.filters import AdminFilter, ChatTypeFilter
from hendlers.mailing import revenue_by_day, safe_boss

from structures.keybords import (
    main_menu,
    boss_report_menu,
    boss_staff_menu,
    boss_other_menu, points_menu_all, remove, employee_menu, cancel_menu, positions,
    yes_no,
    no,
    points_menu_sv, role_menu, boss_main_menu
)

from structures.keybords.cb_makers import create_inline_kb, create_kb

from structures.fsm.admin import (
    EmployeeAdd,
    EmployeeDelete,
    EmployeeUpdate,
    EmployeeActivate,
    PointAdd,
    PointDelete,
    PointUpdate,
    Mailing,
)

from core.bot import bot
from database import User, Database
from structures.role import Role

from utils.check_media import media_create
from utils.utils import get_current_datetime, divide_list, dt_formatted, seconds_to_time
from services.async_google_service import (google_exits, google_add_row, google_update_row, google_authorize_token)

from core.config import settings, GoogleSheetsSettings
from structures.restrictions import Restrictions as Rest

gs: GoogleSheetsSettings = settings.gs

router = Router(name=__name__)
router.message.filter(and_f(AdminFilter(), ChatTypeFilter(['private'])))

statesEmployee = StateFilter(
    EmployeeAdd(),
    EmployeeDelete(),
    EmployeeUpdate(),
    EmployeeActivate(),
)


@router.message(Command("cancel"), statesEmployee)
@router.message(F.text.lower().in_({'отмена', 'отменить', '❌ отмена', '⬆ выйти', 'cancel'}), statesEmployee)
async def cancel_employee_handler(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    user_role_reply_markup = {
        Role.admin: ('Еще вопросы? 👇', boss_staff_menu),
        Role.staff: ('Еще вопросы? 👇', main_menu),
        Role.supervisor: ('Еще вопросы? 👇', main_menu)
    }

    user_id = message.from_user.id
    user_role = await db.user.get_role(user_id=user_id)
    answer_text, reply_markup = user_role_reply_markup.get(user_role)

    await message.answer(answer_text, disable_web_page_preview=True, reply_markup=reply_markup)


statesOther = StateFilter(
    PointAdd(),
    PointDelete(),
    PointUpdate(),
    Mailing(),
)


@router.message(Command("cancel"), statesOther)
@router.message(F.text.lower().in_({'отмена', 'отменить', '❌ отмена', '⬆ выйти', 'cancel'}), statesOther)
async def cancel_other_handler(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    user_role_reply_markup = {
        Role.admin: ('Еще вопросы? 👇', boss_other_menu),
        Role.staff: ('Еще вопросы? 👇', main_menu),
        Role.supervisor: ('Еще вопросы? 👇', main_menu)
    }

    user_id = message.from_user.id
    user_role = await db.user.get_role(user_id=user_id)
    answer_text, reply_markup = user_role_reply_markup.get(user_role)

    await message.answer(answer_text, disable_web_page_preview=True, reply_markup=reply_markup)


@router.message(StateFilter(None), F.text.lower() == '🚹 добавить')
async def employee_add_start(message: Message, state: FSMContext):
    """Добавление нового сотрудника в БД(users)"""
    await state.set_state(EmployeeAdd.USER_ID)
    await message.reply('Введи Telegram id 👇', reply_markup=cancel_menu)


@router.message(StateFilter(EmployeeAdd.USER_ID), F.text)
async def employee_add_user_id(message: Message, state: FSMContext, db: Database):
    user_id = int(message.text.strip())
    user = await db.user.get_one(user_id=user_id)

    if not user:
        await state.update_data(user_id=user_id)
        await state.set_state(EmployeeAdd.FULL_NAME)
        await message.answer('Введи Фамилию и Имя (Иванов Иван) 👇', reply_markup=cancel_menu)
    else:

        staff = (
            f'<b>⚠️ Уже в базе</b>️\n'
            f'{user.full_name}\n'
            f'Должность: {user.position}\n'
            f'Точка: {user.point}\n'
            f'Доступ: {user.role.value}\n'
            f'Активен: {user.status}'
        )

        await message.answer(staff, reply_markup=boss_staff_menu)
        await state.clear()


@router.callback_query(F.data.startswith('employee'), StateFilter(None))
async def employee_add_start_query(query: CallbackQuery, state: FSMContext, db: Database):
    callback_data, user_id = query.data.split('_')
    if callback_data == 'employeeAdd':
        await state.update_data(user_id=int(user_id))
        await state.set_state(EmployeeAdd.FULL_NAME)
        await bot.send_message(query.from_user.id, 'Введи Фамилию и Имя (Иванов Иван) 👇', reply_markup=cancel_menu)
    elif callback_data == 'employeeDelete':
        await db.user.update(user_id=int(user_id), status=False)
        await bot.send_message(query.from_user.id, 'Удалили сотрудника 😈', reply_markup=boss_staff_menu)
        await state.clear()
    elif callback_data == 'employeeCancel':
        await query.message.delete()
        await bot.send_message(user_id, 'Запрос на добавление отклонён!', reply_markup=remove)
        await state.clear()
    else:
        await query.message.delete()
        await bot.send_message(query.from_user.id, 'Что-то пошло не так...', reply_markup=boss_staff_menu)
        await state.clear()


@router.message(StateFilter(EmployeeAdd.FULL_NAME), F.text)
async def employee_add_staff_full_name(message: Message, state: FSMContext):
    last_name, first_name = message.text.strip().split(' ')
    if not last_name or not first_name:
        await message.answer('Введи Фамилию и Имя (Иванов Иван) 👇', reply_markup=cancel_menu)
        return
    await state.update_data(last_name=last_name.capitalize(), first_name=first_name.capitalize())
    await state.set_state(EmployeeAdd.POSITION)
    await message.answer('Должность 👇', reply_markup=positions)


@router.message(StateFilter(EmployeeAdd.POSITION), F.text)
async def employee_add_position(message: Message, state: FSMContext):
    await state.update_data(position=message.text)
    await state.set_state(EmployeeAdd.POINT)
    await message.answer('Выбери точку 👇', reply_markup=await points_menu_all())


@router.message(StateFilter(EmployeeAdd.POINT), F.text)
async def employee_add_point(message: Message, state: FSMContext):
    await state.update_data(point=message.text)
    await state.set_state(EmployeeAdd.ROLE)
    await message.answer('Уровень доступа?', reply_markup=role_menu)


@router.message(StateFilter(EmployeeAdd.ROLE), F.text)
async def employee_add_role(message: Message, state: FSMContext, db: Database):
    role = Role.key(message.text)
    await state.update_data(role=role)

    if role == Role.supervisor.name:
        await state.set_state(EmployeeAdd.POINTS)
        await message.answer('За какие точки отвечает?', reply_markup=await points_menu_sv())
    else:
        await state.update_data(status=True)
        data = await state.get_data()
        await db.user.add(User(**data))

        for suffix in ['']:  # ['', ' П', ' С', ' К']:
            c = lambda: random.randint(0, 255)
            await google_add_row(
                gs.BOOK_TABLE_ID,
                gs.SHEET_STAFF,
                array=[
                    data['last_name'] + suffix,
                    data['position'],
                    data['point'],
                    data['first_name'],
                    data['user_id'],
                    'TRUE',
                    f'{data["last_name"] + suffix} {data["first_name"]}',
                    '#%02X%02X%02X' % (c(), c(), c())
                ]
            )

        await message.answer(
            f'Добавили сотрудника 😁\n'
            f'***************\n'
            f'{data["first_name"]} {data["last_name"]}\n'
            f'Должность: {data["position"]}\n'
            f'Точка: {data["point"]}\n'
            f'Доступ: {message.text}',
            reply_markup=boss_staff_menu
        )
        try:

            user_role_reply_markup = {
                Role.admin: boss_main_menu,
                Role.staff: main_menu,
                Role.supervisor: main_menu
            }

            user_id = data['user_id']
            user_role = await db.user.get_role(user_id=user_id)
            reply_markup = user_role_reply_markup.get(user_role)
            msg = f'Аккаунт активирован ✌\n{data["first_name"]}, теперь ты в команде!!!\nМеню 👇'
            await bot.send_message(user_id, msg, reply_markup=reply_markup)

        except Exception as ex:
            logging.warning("user_id: %s, %s", data["user_id"], ex)
        await state.clear()


@router.message(StateFilter(EmployeeAdd.POINTS), F.text)
async def employee_add_end(message: Message, state: FSMContext, db: Database):
    await state.update_data(points=message.text, status=True)
    data = await state.get_data()
    await db.user.add(User(**data))

    c = lambda: random.randint(0, 255)
    await google_add_row(
        gs.BOOK_TABLE_ID,
        gs.SHEET_STAFF,
        array=[
            data['last_name'],
            data['position'],
            data['point'],
            data['first_name'],
            data['user_id'],
            'TRUE',
            f'{data["last_name"]} {data["first_name"]}',
            '#%02X%02X%02X' % (c(), c(), c())
        ]
    )

    await message.answer(
        f'<b>Добавили сотрудника</b> 😁\n'
        f'{'*' * 15}\n'
        f'{data["first_name"]} {data["last_name"]}\n'
        f'Должность: {data["position"]}\n'
        f'Точка: {data["point"]}\n'
        f'Доступ: {Role[data["role"]].value}\n'
        f'Точки: {data["points"] if data.get("points") is not None else "Нет"}',
        reply_markup=boss_staff_menu
    )
    try:
        await bot.send_message(data['user_id'],
                               f'Аккаунт активирован ✌\n{data["first_name"]}, теперь ты в команде!!!\nМенюшечка 👇',
                               reply_markup=main_menu)
    except Exception as ex:
        logging.warning("user_id: %s, %s", data["user_id"], ex)
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == '🚹 обновить')
async def employee_update_start(message: Message, state: FSMContext):
    """Обновление данных по сотруднику в БД(users)"""
    menu = await employee_menu(False)
    if menu:
        await state.set_state(EmployeeUpdate.USER_ID)
        await message.reply('Выбери сотрудника 👇', reply_markup=menu)
    else:
        await message.reply('Нет сотрудников в базе 😬', reply_markup=boss_staff_menu)


@router.message(StateFilter(EmployeeUpdate.USER_ID), F.text)
async def employee_update_user_id(message: Message, state: FSMContext, db: Database):
    user_id = await db.user.get_user_id_by_full_name(full_name=message.text)
    last_name, first_name = message.text.strip().split(' ')
    await state.update_data(user_id=user_id, first_name=first_name, last_name=last_name)
    await state.set_state(EmployeeUpdate.FULL_NAME)
    await message.answer('Введи Фамилию и Имя (Иванов Иван), для пропуска нажми "Нет"', reply_markup=no)


@router.message(StateFilter(EmployeeUpdate.FULL_NAME), F.text)
async def employee_update_full_name(message: Message, state: FSMContext):
    if message.text != 'Нет':
        last_name, first_name = message.text.strip().split(' ')
        if not last_name or not first_name:
            await message.answer('Введи Фамилию и Имя (Иванов Иван) 👇', reply_markup=cancel_menu)
            return

        await state.update_data(last_name=last_name.capitalize(), first_name=first_name.capitalize())

    await state.set_state(EmployeeUpdate.POSITION)
    await message.answer('Выбери должность', reply_markup=positions)


@router.message(StateFilter(EmployeeUpdate.POSITION), F.text)
async def employee_update_position(message: Message, state: FSMContext):
    await state.update_data(position=message.text)
    await state.set_state(EmployeeUpdate.POINT)
    await message.answer('Выбери точку 👇', reply_markup=await points_menu_all())


@router.message(StateFilter(EmployeeUpdate.POINT), F.text)
async def employee_update_point(message: Message, state: FSMContext):
    await state.update_data(point=message.text)
    await state.set_state(EmployeeUpdate.ROLE)
    await message.answer('Уровень доступа?', reply_markup=role_menu)


@router.message(StateFilter(EmployeeUpdate.ROLE), F.text)
async def employee_update_role(message: Message, state: FSMContext, db: Database):
    role = Role.key(message.text)
    await state.update_data(role=role)

    if role == Role.supervisor.name:
        await state.set_state(EmployeeUpdate.POINTS)
        await message.answer('За какие точки отвечает?', reply_markup=await points_menu_sv())
    else:
        await state.update_data(points=None, status=True)
        data = await state.get_data()
        await db.user.update(**data)

        await google_update_row(
            gs.BOOK_TABLE_ID,
            gs.SHEET_STAFF,
            array=[[data['position'], data['point']]],
            query=str(data['user_id']),
            col=5,
            col_s='B',
            col_f='C')

        await message.answer(
            f'<b>Обновили сотрудника</b> 😁\n'
            f'{'*'*15}\n'
            f'{data["last_name"]} {data["first_name"]}\n'
            f'Должность: {data["position"]}\n'
            f'Точка: {data["point"]}\n'
            f'Доступ: {Role[data["role"]].value}\n'
            f'Точки: {data["points"] if data["points"] is not None else "Нет"}',
            reply_markup=boss_staff_menu
        )

        await state.clear()


@router.message(StateFilter(EmployeeUpdate.POINTS), F.text)
async def employee_update_end(message: Message, state: FSMContext, db: Database):
    await state.update_data(points=message.text, status=True)
    data = await state.get_data()
    await db.user.update(**data)

    await google_update_row(
        gs.BOOK_TABLE_ID,
        gs.SHEET_STAFF,
        array=[[data['position'], data['point']]],
        query=str(data['user_id']),
        col=5,
        col_s='B',
        col_f='C')

    await message.answer(
        f'<b>Обновили сотрудника</b> 😁\n'
        f'{'*' * 15}\n'
        f'{data["last_name"]} {data["first_name"]}\n'
        f'Должность: {data["position"]}\n'
        f'Точка: {data["point"]}\n'
        f'Доступ: {Role[data["role"]].value}\n'
        f'Точки: {data["points"] if data["points"] is not None else "Нет"}',
        reply_markup=boss_staff_menu
    )

    await state.clear()


@router.message(StateFilter(None), F.text.lower() == '🚹 удалить')
async def employee_delete_start(message: Message, state: FSMContext):
    """Удаление сотрудника из БД(users)"""
    menu = await employee_menu()
    if menu:
        await message.reply('Выбери сотрудника 👇', reply_markup=menu)
        await state.set_state(EmployeeDelete.FULL_NAME)
    else:
        await message.reply('Никого нет дома 😬', reply_markup=boss_staff_menu)


@router.message(StateFilter(EmployeeDelete.FULL_NAME), F.text)
async def employee_delete_end(message: Message, state: FSMContext, db: Database):
    user_id = await db.user.get_user_id_by_full_name(full_name=message.text)
    # await db.user.delete(user_id=user_id)
    await db.user.update(user_id=user_id, status=False)

    await google_update_row(
        gs.BOOK_TABLE_ID,
        gs.SHEET_STAFF,
        array=[['FALSE']],
        query=str(user_id),
        col=5,
        col_s='F',
        col_f='F'
    )

    await message.answer('Удалили сотрудника 😈', reply_markup=boss_staff_menu)
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == '🚹 активировать')
async def employee_activate_start(message: Message, state: FSMContext):
    """Активация удаленного сотрудника в БД(users)"""
    menu = await employee_menu(False)
    if menu:
        await state.set_state(EmployeeActivate.FULL_NAME)
        await message.reply('Выбери сотрудника 👇', reply_markup=menu)
    else:
        await message.reply('Не активных нет 😬', reply_markup=boss_staff_menu)


@router.message(StateFilter(EmployeeActivate.FULL_NAME), F.text)
async def employee_activate_end(message: Message, state: FSMContext, db: Database):
    user_id = await db.user.get_user_id_by_full_name(full_name=message.text)
    await db.user.update(user_id=user_id, is_active=True)
    await message.answer('Активировали 👍', reply_markup=boss_staff_menu)
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == '✅ добавить точку')
async def point_add(message: Message, state: FSMContext):
    """Добавление новой точки"""
    await state.set_state(PointAdd.NAME)
    await message.answer('Введи название новой точки 👇', reply_markup=remove)


@router.message(StateFilter(PointAdd.NAME), F.text)
async def point_add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    # await message.answer('Введи адрес 👇', reply_markup=remove)
    # await state.set_state(PointAdd.address)
    await state.set_state(PointAdd.ALIAS)
    await message.answer('Введи алиас (Балашиха > b) 👇', reply_markup=remove)


# @router.message(StateFilter(PointAdd.address), F.text)
# async def point_add_address(message: Message, state: FSMContext):
#     await state.update_data(address=message.text.strip())
#     await message.answer('Введи координаты (широта)👇', reply_markup=remove)
#     await state.set_state(PointAdd.latitude)
#
#
# @router.message(StateFilter(PointAdd.latitude), F.text)
# async def point_add_latitude(message: Message, state: FSMContext):
#     await state.update_data(latitude=message.text.strip())
#     await message.answer('Введи координаты (долгота)👇', reply_markup=remove)
#     await state.set_state(PointAdd.longitude)
#
#
# @router.message(StateFilter(PointAdd.longitude), F.text)
# async def point_add_longitude(message: Message, state: FSMContext):
#     await state.update_data(longitude=message.text.strip())
#     await message.answer('Введи алиас 👇', reply_markup=remove)
#     await state.set_state(PointAdd.alias)


@router.message(StateFilter(PointAdd.ALIAS), F.text)
async def point_add_end(message: Message, state: FSMContext, db: Database):
    await state.update_data(alias=message.text.strip())
    data = await state.get_data()
    await db.point.add(Point(**data))
    await message.answer(f'Добавили точку ✌', reply_markup=boss_other_menu)
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == '❌ удалить точку')
async def point_delete_start(message: Message, state: FSMContext):
    await state.set_state(PointDelete.NAME)
    await message.answer('Выбери точку', reply_markup=await points_menu_all())


@router.message(StateFilter(PointDelete.NAME), F.text)
async def point_delete_end(message: Message, state: FSMContext, db: Database):
    """Удаление точки"""
    # await db.point_update(session, name=message.text, status=False)
    await db.point.delete(name=message.text)
    await message.answer(f'Удалили точку ✌', reply_markup=boss_other_menu)
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == '📢 рассылка')
async def news_mailing_start(message: Message, state: FSMContext):
    """Массовая рассылка сообщений по сотрудникам"""
    await state.set_state(Mailing.TEXT)
    await message.reply('Введи текст рассылки 👇', reply_markup=cancel_menu)


@router.message(StateFilter(Mailing.TEXT), F.text | F.video | F.video_note)
async def news_mailing(message: Message, state: FSMContext, db: Database):
    """Рассылка по сотрудникам"""
    users = await db.user.get_all()
    check = []
    text = message.text
    if text:
        msg = f'📢 <b>News {get_current_datetime().strftime("%d.%m.%y %H:%M")}</b>\n<em>{text}</em>'
        for user in users:
            try:
                if user.status and user.user_id not in check:
                    check.append(user.user_id)
                    await bot.send_message(user.user_id, msg)
            except Exception as ex:
                logging.warning("%s %s ошибка рассылки", user.user_id, user.full_name, exc_info=ex)
                continue
    elif message.video:
        for user in users:
            try:
                msg = f'📢 <b>News {get_current_datetime().strftime("%d.%m.%y %H:%M")}</b>\n' \
                      f'<em>просмотри видео сообщение 👇</em>'
                if user.status and user.user_id not in check:
                    check.append(user.user_id)
                    await bot.send_video(chat_id=user.user_id, video=message.video.file_id, caption=msg)
            except Exception as ex:
                logging.warning("%s %s ошибка рассылки", user.user_id, user.full_name, exc_info=ex)
                continue
    elif message.video_note:
        for user in users:
            try:
                msg = f'📢 <b>News {get_current_datetime().strftime("%d.%m.%y %H:%M")}</b>\n' \
                      f'<em>просмотри видео сообщение 👇</em>'
                if user.status and user.user_id not in check:
                    check.append(user.user_id)
                    await bot.send_message(user.user_id, msg)
                    await bot.send_video_note(
                        chat_id=user.user_id,
                        video_note=message.video_note.file_id,
                        duration=47,
                        length=360)
            except Exception as ex:
                logging.warning("%s %s ошибка рассылки", user.user_id, user.full_name, exc_info=ex)
                continue

    await message.answer('Рассылку провели 😎', reply_markup=boss_other_menu)
    await state.clear()


@router.message(F.text.lower().in_({'📸 за сегодня', '📸 за вчера'}))
async def send_reports(message: Message, db: Database):
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        date = None
        if message.text == '📸 За сегодня':
            date = dt_formatted(6)
        elif message.text == '📸 За вчера':
            date = dt_formatted(6, minus_days=1)

        reports_by_date = await db.check_day.get_reports_by_date(date=date)
        reports = [report for report in reports_by_date]

        if len(reports) > 0:
            for report in reports:
                add_date = report.add_date
                report_type = report.type
                point = report.point
                employee = report.user.full_name
                files = report.files_id.split(', ')
                verified = "Да" if report.verified else "Нет"
                comment = report.comment

                caption = (
                    f'<b>{report_type}</b> ({pytils.dt.ru_strftime(u"%d %B %Y", inflected=True, date=add_date)})\n'
                    f'{"*" * 25}\n'
                    f'Точка: {point}\n'
                    f'Сотрудник: {employee}\n'
                    f'Проверен: {verified}\n'
                    f'Комментарий: {comment}')

                media = await media_create(files, caption)
                await message.answer_media_group(media=media, allow_sending_without_reply=True)

            await message.answer('Данные отправлены ☝', reply_markup=boss_report_menu)
        else:
            await message.reply('Нет данных 😬', reply_markup=boss_report_menu)


@router.message(F.text.lower() == 'кто, где сегодня')
async def today_all_schedule(message: Message):
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        data = await google_exits(offset=0, boss=True)
        await message.answer(text=data, allow_sending_without_reply=True, reply_markup=boss_staff_menu)


@router.message(F.text.lower() == 'кто, где завтра')
async def tomorrow_all_schedule(message: Message):
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        data = await google_exits(offset=1, boss=True)
        if len(data) > Rest.MESSAGE_LENGTH:
            data = divide_list(data.split('***************'), 40)
            for item in data:
                await message.answer(text='***************'.join(item),
                                     allow_sending_without_reply=True,
                                     reply_markup=boss_staff_menu)
        else:
            await message.answer(text=data, allow_sending_without_reply=True, reply_markup=boss_staff_menu)


@router.message(F.text.lower() == 'выходы 7 дней')
async def week_all_schedule(message: Message):
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        data = await google_exits(offset=7, boss=True)
        if len(data) > Rest.MESSAGE_LENGTH:
            data = divide_list(data.split('***************'), 40)
            for item in data:
                await message.answer(text='***************'.join(item),
                                     allow_sending_without_reply=True,
                                     reply_markup=boss_staff_menu)
        else:
            await message.answer(text=data, allow_sending_without_reply=True, reply_markup=boss_staff_menu)


@router.message(F.text.lower().in_({'📈 за сегодня'}))
async def report_by_day(message: Message, db: Database):
    """Отчет по отправленным за день"""
    date = dt_formatted(6)

    reports = await db.check_day.get_reports_by_period(date, date)
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

    reports = await db.check_day.get_reports_by_period(start_date, end_date)

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

@router.message(F.text.lower() == '💰 выручка за вчера')
async def send_yesterday_revenue(message: Message):
    """Выручка за вчера"""
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        await revenue_by_day(message.from_user.id)


@router.message(F.text.lower() == '💵 остатки сейф')
async def send_safe(message: Message):
    """Остатки сейф на сегодня"""
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        await safe_boss(message.from_user.id, reply_markup=boss_report_menu)

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
