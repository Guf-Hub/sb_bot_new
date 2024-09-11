import logging

from aiogram import Router, F
from aiogram.filters import Command, and_f, StateFilter
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender
from aiogram.fsm.context import FSMContext

from filters.filters import AdminFilter, ChatTypeFilter
from hendlers.mailings.mailing import revenue_by_day, safe_boss

from structures.keybords import (
    boss_other_menu,
    cancel_menu, boss_report_menu
)

from fsm.mailings import Mailing

from core.bot import bot
from database import Database
from utils.utils import get_current_datetime
from core.config import settings, GoogleSheetsSettings

gs: GoogleSheetsSettings = settings.gs

router = Router(name=__name__)
router.message.filter(and_f(AdminFilter(), ChatTypeFilter(['private'])))

statesMailing = StateFilter(
    Mailing(),
)


@router.message(Command("cancel"), statesMailing)
@router.message(F.text.lower().in_({'отмена', 'отменить', '❌ отмена', '⬆ выйти', 'cancel'}), statesMailing)
async def cancel_other_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    answer_text, reply_markup = ('Еще вопросы? 👇', boss_other_menu)
    await message.answer(answer_text, disable_web_page_preview=True, reply_markup=reply_markup)


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
