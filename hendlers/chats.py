#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os

from aiogram import Router, F
from aiogram.filters import Command, CommandStart, or_f, and_f
from aiogram.types import (Message, FSInputFile)
from aiogram.utils.chat_action import ChatActionSender
from aiogram.fsm.context import FSMContext

from common.questions import help_msg
from core.config import settings
from database import Database, User
from filters.filters import ChatTypeFilter

from structures.keybords import (
    main_menu,
    boss_main_menu,
    boss_report_menu,
    boss_staff_menu,
    boss_payments_menu,
    boss_other_menu
)
from structures.keybords.cb_makers import create_inline_kb

from core.bot import bot
from utils.utils import get_user_role

# from services.questions import help_msg


router = Router(name=__name__)
router.message.filter(ChatTypeFilter(['private']))


@router.message(CommandStart())
async def start_command(message: Message, db: Database):
    user_id = message.from_user.id
    first_name = message.from_user.first_name if message.from_user.first_name else None

    # if not await db.user_get(session, user_id=user_id):
    if not await db.user.is_exist(user_id=user_id):
        last_name = message.from_user.last_name if message.from_user.last_name else None

        # await db.user.add(
        #     User(
        #         user_id=user_id,
        #         status=False
        #     )
        # )

        inline = create_inline_kb(
            btns={'✅ Добавить?': f'employeeAdd_{user_id}', '❌ Отмена': f'employeeCancel_{user_id}'},
        )

        msg = f'Запрос на добавление:\n{user_id}\n{first_name}\n{last_name}'
        hr = await db.user.get_hr()

        if hr:
            await bot.send_message(hr.user_id, text=msg, reply_markup=inline)
        else:
            await bot.send_message(settings.bot.MASTER, text=msg, reply_markup=inline)

        welcome_msg = (f'Привет, {first_name} 👋'
                       f'Добро пожаловать в команду Sorry Бабушка. '
                       f'Я бот помощник, запишу рабочую инфу. '
                       f'Ждем активации от Александры @sasha_izy, для дальнейшей работы.')

        await message.answer(welcome_msg)

    else:
        user_role_reply_markup = {
            "boss": ('Менюшечка 👇', boss_main_menu),
            "staff": ('Менюшечка 👇', main_menu)
        }

        user_role = await get_user_role(user_id)
        answer_text, reply_markup = user_role_reply_markup[user_role]
        await message.answer(answer_text, disable_web_page_preview=True, reply_markup=reply_markup)


@router.message(F.text.lower().in_({'⬇ персонал'}) & F.from_user.id.in_(set(settings.bot.BOSS)))
async def boss_staff(message: Message):
    await message.answer('Выбери нужное 👇', reply_markup=boss_staff_menu)


@router.message(F.text.lower().in_({'⬇ отчёты'}) & F.from_user.id.in_(set(settings.bot.BOSS)))
async def boss_report(message: Message):
    await message.answer('Выбери нужное 👇', reply_markup=boss_report_menu)


@router.message(F.text.lower().in_({'⬇ расходы'}) & F.from_user.id.in_(set(settings.bot.BOSS)))
async def boss_payments(message: Message):
    await message.answer('Выбери нужное 👇', reply_markup=boss_payments_menu)


@router.message(F.text.lower().in_({'⬇ прочее'}) & F.from_user.id.in_(set(settings.bot.BOSS)))
async def boss_other(message: Message):
    await message.answer('Выбери нужное 👇', reply_markup=boss_other_menu)


@router.message(and_f(Command("log", "db_sqlite", "del"), (F.from_user.id == settings.bot.MASTER)))
async def commands_admin(message: Message):
    user_id = message.from_user.id
    text = message.text.lower()

    if user_id in settings.bot.ADMINS or user_id in settings.bot.BOSS:

        async with ChatActionSender.typing(chat_id=user_id, bot=bot):

            if text == '/log':
                return await message.answer_document(
                    FSInputFile('app.log', filename='app.log'))
            elif text == '/db_sqlite':
                return await message.answer_document(
                    FSInputFile(os.path.join(os.getcwd(), 'database', 'bot.db'), filename='bot.db'))
            elif text == '/del' and user_id == settings.bot.MASTER:
                ...
                # return await mailing.drop_records()


@router.message(or_f(Command("help"), (F.text.lower().in_({'📌 справка'}))))
async def command_help(message: Message):
    """This function handles the command "help" and sends the help message to the user."""
    user_id = message.from_user.id

    user_role_reply_markup = {
        "boss": (help_msg['boss'], boss_main_menu),
        "staff": (help_msg['main'], main_menu)
    }

    user_role = await get_user_role(user_id)
    answer_text, reply_markup = user_role_reply_markup[user_role]
    await message.answer(answer_text, disable_web_page_preview=True, reply_markup=reply_markup)


@router.message(Command("my_id"))
async def command_my_id(message: Message):
    """This function handles the command "my_id" and sends the user's Telegram id as a message."""
    user_id = message.from_user.id
    answer_text = f'Твой Telegram id: {user_id}'
    await message.answer(answer_text, disable_web_page_preview=True)



