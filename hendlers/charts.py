from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from database import Database
from filters.filters import ChatTypeFilter
from core.bot import bot
from services.async_google_service import google_exits
from structures.restrictions import Restrictions as Rest
from structures.keybords import main_menu

from utils.utils import divide_list

router = Router(name=__name__)
router.message.filter(ChatTypeFilter(['private']))


@router.message(F.text.lower() == '📈 график неделя')
async def week_schedule(message: Message, db: Database):
    """График на неделю"""
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        user = await db.user.get_one(user_id=message.from_user.id)
        data = await google_exits(offset=7, employee=user.last_name)

        if len(data) > Rest.MESSAGE_LENGTH:
            data = divide_list(data.split('***************'), 40)
            for item in data:
                await message.answer(text='***************'.join(item),
                                     allow_sending_without_reply=True,
                                     reply_markup=main_menu)
        else:
            await message.answer(text=data, allow_sending_without_reply=True, reply_markup=main_menu)


@router.message(F.text.lower() == '📈 график месяц')
async def month_schedule(message: Message, db: Database):
    """График на месяц"""
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        user = await db.user.get_one(user_id=message.from_user.id)
        data = await google_exits(offset=30, employee=user.last_name)

        if len(data) > Rest.MESSAGE_LENGTH:
            data = divide_list(data.split('***************'), 40)
            for item in data:
                await message.answer(text='***************'.join(item),
                                     allow_sending_without_reply=True,
                                     reply_markup=main_menu)
        else:
            await message.answer(text=data, allow_sending_without_reply=True, reply_markup=main_menu)
