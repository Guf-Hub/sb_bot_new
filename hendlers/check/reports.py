import pytils

from aiogram import Router, F
from aiogram.filters import and_f
from aiogram.types import (Message)
from aiogram.utils.chat_action import ChatActionSender

from filters.filters import ChatTypeFilter, ActiveFilter

from structures.keybords import (
    boss_report_menu
)

from core.bot import bot
from database import Database

from utils.check_media import media_create
from utils.utils import dt_formatted

from core.config import settings, GoogleSheetsSettings

gs: GoogleSheetsSettings = settings.gs

router = Router(name=__name__)
router.message.filter(and_f(ActiveFilter(), ChatTypeFilter(['private'])))


@router.message(F.text.lower().in_({'📸 за сегодня', '📸 за вчера'}))
async def send_reports(message: Message, db: Database):
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        date = None
        if message.text == '📸 За сегодня':
            date = dt_formatted(6)
        elif message.text == '📸 За вчера':
            date = dt_formatted(6, minus_days=1)

        reports_by_date = await db.check_cafe.get_reports_by_date(date=date)
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
