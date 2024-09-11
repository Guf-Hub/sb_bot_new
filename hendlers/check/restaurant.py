import logging
import time
from datetime import datetime, timezone

import pytils
from aiogram import Router, F
from aiogram.fsm.context import FSMContext

from aiogram.filters import StateFilter, Command
from aiogram.types import (CallbackQuery, Message, FSInputFile)
from aiogram.utils.chat_action import ChatActionSender

from core.bot import bot
from core.config import settings, GoogleSheetsSettings, TgBot
from database import CheckDay, Database

from filters.filters import ChatTypeFilter
from structures.keybords.cb_makers import create_inline_kb

from structures.keybords import (
    main_menu,
    boss_report_menu,
    remove,
    morning_type_menu,
    points_menu,
    all_ok,
    ok,
    boss_main_menu,
)

from fsm.restaurant import RestaurantMorning, RestaurantEvening, CheckRestaurantReport

from services.async_google_service import google_exits_by_point
from common.questions import check_q, BIG_CONFIG
from structures.role import Role

from utils.utils import dt_formatted, get_current_datetime, time_in_range
from utils.check_media import media_create

tg: TgBot = settings.bot
g: GoogleSheetsSettings = settings.gs

router = Router(name=__name__)
router.message.filter(ChatTypeFilter(['private']))

states = StateFilter(
    RestaurantMorning(),
    RestaurantEvening(),
    CheckRestaurantReport(),
)


@router.message(Command("cancel"), states)
@router.message(F.text.lower().in_({'отмена', 'отменить', '❌ отмена', '⬆ выйти', 'cancel'}), states)
async def cancel_check_day_handler(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    user_role_reply_markup = {
        Role.admin: ('Еще вопросы? 👇', boss_report_menu),
        Role.staff: ('Еще вопросы? 👇', main_menu),
        Role.supervisor: ('Еще вопросы? 👇', main_menu)
    }

    user_id = message.from_user.id
    user_role = await db.user.get_role(user_id=user_id)
    answer_text, reply_markup = user_role_reply_markup.get(user_role)

    await message.answer(answer_text, disable_web_page_preview=True, reply_markup=reply_markup)


class PhotoPath:
    """Класс для получения пути к планограмме для конкретной точки"""

    def __init__(self, point: str, db: Database):
        self.point = point
        self.db = db

    async def set(self) -> str:
        alias = await self.db.point.get_alias(name=self.point)
        if alias:
            return BIG_CONFIG[f'{alias}']['plan']
        raise AttributeError(f"Нет планограммы: '{self.point}'")


async def is_unique(message: Message, point: str, report_type: str, db: Database, date: str = None) -> bool:
    check = await db.check_restaurant.is_unique_report_by_date(
        point=point,
        report_type=report_type,
        date=date if date else dt_formatted(6)
    )

    if check:
        user = await db.user.get_one_by_pk(pk=check.user_id)
        reply_markup = boss_report_menu if message.from_user.id in tg.BOSS else main_menu
        await message.answer(
            f'<b>"{report_type}"</b> за {date if date else dt_formatted(1)} уже есть!!!\n'
            f'Добавил: {user.full_name}',
            reply_markup=reply_markup
        )
        return True

    return False


@router.message(StateFilter(None), F.text.lower() == '✅ утренний')
async def morning_start(message: Message, state: FSMContext, db: Database):
    user_id = message.from_user.id
    user = await db.user.get_one(user_id=user_id)
    if not user:
        await state.clear()
        return await message.answer(f'Пользователя {user_id} нет в базе, добавьте себя, назначьте права!!!')
    await state.update_data(user_id=user.id)
    await state.set_state(RestaurantMorning.type_key)
    await message.reply('Выбери 👇', reply_markup=morning_type_menu)


@router.message(StateFilter(RestaurantMorning.type_key), F.text)
async def morning_type_key(message: Message, state: FSMContext):
    if message.text in ['Настройка', 'До 10', 'До 12']:
        await state.update_data(type_key=message.text)
        await state.set_state(RestaurantMorning.point)
        await message.reply('Выбери точку 👇', reply_markup=await points_menu())
    else:
        await message.reply('Выбери 👇', reply_markup=morning_type_menu)


@router.message(StateFilter(RestaurantMorning.point), F.text)
async def morning_point(message: Message, state: FSMContext, db: Database):
    point = message.text
    if await db.point.get_one(name=point):
        user_id = message.from_user.id

        await state.update_data(point=point)

        data = await state.get_data()
        type_key = data.get('type_key')

        if type_key in ['До 10', 'До 12']:
            await state.update_data(question_one=None)

        if type_key == 'Настройка':
            await state.update_data(type='Настройка')
            await state.set_state(RestaurantMorning.question_one)
            await message.answer(check_q['cf_1'], reply_markup=all_ok)
        elif type_key == 'До 10':
            if await is_unique(message, point, report_type='Утренний до 10', db=db):
                await state.clear()
            else:
                async with ChatActionSender.upload_photo(chat_id=user_id, bot=bot):
                    await state.update_data(type='Утренний до 10')
                    await state.set_state(RestaurantMorning.file1)
                    photo = FSInputFile(await PhotoPath(point, db).set(), filename=f'{point}_plane.png')
                    await message.answer_photo(caption=check_q['mq_1'], photo=photo, reply_markup=remove)
        elif type_key == 'До 12':
            if await is_unique(message, point, report_type='Утренний до 12', db=db):
                await state.clear()
            else:
                await state.update_data(type='Утренний до 12')
                await state.set_state(RestaurantMorning.file3)
                await message.answer(check_q['mq_3'], reply_markup=remove)
    else:
        await message.answer('Похоже ты ошибся, выбери точку 👇', reply_markup=await points_menu())


@router.message(StateFilter(RestaurantMorning.question_one), F.text)
async def morning_q1(message: Message, state: FSMContext):
    data = await state.get_data()
    type_key = data.get('type_key')

    if type_key == 'Настройка':
        await state.update_data(question_one=message.text)
        await state.set_state(RestaurantMorning.file1)
        await message.answer(check_q['cf_2'], reply_markup=remove)
    else:
        await message.answer(check_q['cf_1'], reply_markup=all_ok)


@router.message(StateFilter(RestaurantMorning.file1), F.photo)
async def morning_file1(message: Message, state: FSMContext, db: Database):
    """`Настройка`"""
    user_id = message.from_user.id
    await state.update_data(file1=message.photo[-1].file_id)

    data = await state.get_data()
    type_key = data.get('type_key')
    point = data.get('point')

    if type_key == 'Настройка':

        user = await db.user.get_one(user_id=user_id)

        msg = f'<b>Настройка эспрессо</b>\n' \
              f'{pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=get_current_datetime())}\n' \
              f'{"*" * 25}\n' \
              f'Точка: <b>{point}</b>\n' \
              f'Сотрудник: {user.full_name}\n' \
              f'Сейф: {data["question_one"]}\n' \
              f'#Утренний_Эспрессо_{point}'

        await message.answer_photo(photo=data['file1'], caption=msg, allow_sending_without_reply=True)

        supervisors = await db.user.get_supervisors()
        supervisor = next((sv for sv in supervisors if point in sv.points.split(', ')), None)

        if supervisor and supervisor.user_id != user_id:
            supervisor_id = supervisor.user_id
            try:
                await bot.send_photo(
                    supervisor_id,
                    photo=data['file1'],
                    caption=msg,
                    allow_sending_without_reply=True
                )
                logging.info(
                    f'"Утренний" эспрессо {point} '
                    f'отправлен {supervisor_id} {supervisor.full_name}, {dt_formatted()}')
            except Exception as e:
                logging.warning(f'{supervisor_id} {supervisor.full_name} > {e}')

        await send_other_staff(message, photo=data['file1'], msg=msg)

        reply_markup = boss_report_menu if user_id in tg.BOSS else main_menu
        await message.answer('Отправили на проверку 👍', reply_markup=reply_markup)
        await state.clear()
    elif type_key == 'До 10':
        await state.set_state(RestaurantMorning.file2)
        await message.answer(check_q['mq_2'])


@router.message(StateFilter(RestaurantMorning.file2), F.photo)
async def morning_file2(message: Message, state: FSMContext, db: Database):
    """`Утренний до 10`"""
    user_id = message.from_user.id

    async with ChatActionSender.typing(chat_id=user_id, bot=bot):

        user = await db.user.get_one(user_id=user_id)
        await state.update_data(file2=message.photo[-1].file_id)

        data = await state.get_data()
        point = data.get('point')
        report_type = data.get('type')

        add_date = get_current_datetime().date()
        in_time = time_in_range(period=1)

        supervisors = await db.user.get_supervisors()
        supervisor = next((sv for sv in supervisors if point in sv.points.split(', ')), None)

        files_id = ', '.join([data['file1'], data['file2']])

        report_id = await db.check_restaurant.add(
            CheckDay(
                add_date=add_date,
                type=report_type,
                point=point,
                user_id=data.get('user_id'),
                files_id=files_id,
                in_time=in_time,
                supervisor=supervisor.last_name if supervisor else None,
            )
        )

        logging.info("State: %s\n", data)
        logging.info(f'"{report_type}" {report_id=} {point} за {add_date} добавлен, отправил > {user.full_name}')

        caption = f'<b>{report_type}</b>\n' \
                  f'{pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=get_current_datetime())}\n' \
                  f'{"*" * 25}\n' \
                  f'Точка: <b>{point}</b>\n' \
                  f'Сотрудник: {user.full_name}\n' \
                  f'Проверен: Нет\n' \
                  f'#{report_type.replace(" ", "_")}_{point}'

        media = await media_create(data, caption)
        await message.answer_media_group(media=media, allow_sending_without_reply=True)

        reply_markup = boss_report_menu if user_id in tg.BOSS else main_menu
        await message.answer('Отправили на проверку 👍', reply_markup=reply_markup)

    if supervisor:
        supervisor_id = supervisor.user_id

        kb = create_inline_kb(
            btns={'✅ Подтвердить?': f'checkRestaurantReport_{report_id}'},
        )

        try:
            await bot.send_media_group(supervisor_id, media=media, allow_sending_without_reply=True)
            await bot.send_message(supervisor_id, 'После просмотра, нажми кнопку для подтверждения 👇',
                                   reply_markup=kb)
            logging.info(
                f'"{report_type}" {point} на проверке у {supervisor_id} {supervisor.full_name}, {dt_formatted()}')
        except Exception as e:
            logging.warning(f'{supervisor_id} {supervisor.full_name} > {e}')

    await state.clear()


@router.message(StateFilter(RestaurantMorning.file3), F.video)
async def morning_file3(message: Message, state: FSMContext, db: Database):
    """`Утренний до 12`"""
    user_id = message.from_user.id
    async with ChatActionSender.typing(chat_id=user_id, bot=bot):
        user = await db.user.get_one(user_id=user_id)

        await state.update_data(file3=message.video.file_id)

        data = await state.get_data()
        point = data.get('point')
        report_type = data.get('type')

        add_date = get_current_datetime().date()
        in_time = time_in_range(period=1)

        supervisors = await db.user.get_supervisors()
        supervisor = next((sv for sv in supervisors if point in sv.points.split(', ')), None)

        files_id = data.get('file3')

        report_id = await db.check_restaurant.add(
            CheckDay(
                add_date=add_date,
                type=report_type,
                point=point,
                user_id=data.get('user_id'),
                question_one=data.get('question_one'),
                files_id=files_id,
                in_time=in_time,
                supervisor=supervisor.last_name if supervisor else None,
            )
        )

        logging.info(data)
        logging.info(f'"{report_type}" {report_id=} {point} за {add_date} добавлен, отправил > {user.full_name}')

        caption = f'<b>{report_type}</b>\n' \
                  f'{pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=get_current_datetime())}\n' \
                  f'{"*" * 25}\n' \
                  f'Точка: <b>{point}</b>\n' \
                  f'Сотрудник: {user.full_name}\n' \
                  f'Проверен: Нет\n' \
                  f'#{report_type.replace(" ", "_")}_{point}'

        media = await media_create(data, caption)
        await message.answer_media_group(media=media, allow_sending_without_reply=True)

        reply_markup = boss_report_menu if user_id in tg.BOSS else main_menu
        await message.answer('Отправили на проверку 👍', reply_markup=reply_markup)

    if supervisor:
        supervisor_id = supervisor.user_id

        kb = create_inline_kb(
            btns={'✅ Подтвердить?': f'checkRestaurantReport_{report_id}'},
        )

        try:
            await bot.send_media_group(supervisor_id, media=media, allow_sending_without_reply=True)
            await bot.send_message(supervisor_id, 'После просмотра, нажми кнопку для подтверждения 👇',
                                   reply_markup=kb)
            logging.info(
                f'"{report_type}" {point} на проверке у {supervisor_id} {supervisor.full_name}, {dt_formatted()}')
        except Exception as e:
            logging.warning(f'{supervisor_id} {supervisor.full_name} > {e}')

    await state.clear()


@router.message(StateFilter(None), F.text.lower() == '✅ вечерний')
async def evening_start(message: Message, state: FSMContext, db: Database):
    """Вечерний отчет старт"""
    user_id = message.from_user.id
    user = await db.user.get_one(user_id=user_id)
    if not user:
        await state.clear()
        return await message.answer(f'Пользователя {user_id} нет в базе, добавьте себя, назначьте права!!!')

    await state.update_data(user_id=user.id)
    await state.set_state(RestaurantEvening.date)
    date_start = dt_formatted(1)
    date_end = dt_formatted(1, minus_days=1)

    dates_inline = create_inline_kb(btns={
        f'За сегодня ({date_start})': f'eveningDate_{date_start}',
        f'За вчера ({date_end})': f'eveningDate_{date_end}',
    })

    await message.reply('За какой день отчёт?', reply_markup=dates_inline)


@router.callback_query(F.data.startswith('eveningDate'), StateFilter(RestaurantEvening.date))
async def evening_date(query: CallbackQuery, state: FSMContext, db: Database):
    """Проверка выбора даты в вечернем отчёте"""

    user_id = query.from_user.id
    user = await db.user.get_one(user_id=user_id)

    if user and user.status:
        answer_data = query.data
        date = answer_data.split('_')[1]
        await state.update_data(date=date, type='Вечерний')
        await state.set_state(RestaurantEvening.point)
        await query.message.delete()
        await bot.send_message(user_id, f'Отчет за: {date}')
        await bot.send_message(user_id, 'Выбери точку 👇', reply_markup=await points_menu())
    else:
        await query.message.delete()
        await bot.send_message(user_id, 'Нет доступа', reply_markup=remove)


@router.message(StateFilter(RestaurantEvening.point), F.text)
async def evening_point(message: Message, state: FSMContext, db: Database):
    point = message.text
    if await db.point.get_one(name=point):
        await state.update_data(point=point)
        data = await state.get_data()
        date = datetime.strptime(data['date'], '%d.%m.%Y').strftime('%Y-%m-%d')

        if await is_unique(message, point, report_type=data.get('type'), date=date, db=db):
            await state.clear()
        else:
            await state.set_state(RestaurantEvening.file1)
            await message.answer(check_q['ev_1'], reply_markup=remove)
    else:
        await message.answer('Похоже ты ошибся, выбери точку 👇', reply_markup=await points_menu())


@router.message(StateFilter(RestaurantEvening.file1), F.video | F.photo | F.document | F.text)
async def evening_file1(message: Message, state: FSMContext):
    if message.video:
        await state.update_data(file1=message.video.file_id)
        await state.set_state(RestaurantEvening.file2)
        await message.answer(check_q['ev_2'])
    else:
        await message.answer('Загрузи одно видео!!!')


@router.message(StateFilter(RestaurantEvening.file2), F.video | F.photo | F.document | F.text)
async def evening_file2(message: Message, state: FSMContext):
    if message.video:
        await state.update_data(file2=message.video.file_id)
        await state.set_state(RestaurantEvening.file3)
        await message.answer(check_q['ev_3'])
    else:
        await message.answer('Загрузи одно видео!!!')


@router.message(StateFilter(RestaurantEvening.file3), F.video | F.photo | F.document | F.text)
async def evening_file3(message: Message, state: FSMContext, db: Database):
    if message.video:

        user_id = message.from_user.id
        async with ChatActionSender.typing(chat_id=user_id, bot=bot):

            user = await db.user.get_one(user_id=user_id)
            await state.update_data(file3=message.video.file_id)

            data = await state.get_data()
            date = data.get('date')

            weekday = pytils.dt.ru_strftime(u'%A', inflected=True, date=datetime.strptime(date, '%d.%m.%Y'))

            if weekday != 'понедельник':

                point = data.get('point')

                supervisors = await db.user.get_supervisors()
                supervisor = next((sv for sv in supervisors if point in sv.points.split(', ')), None)

                add_date = datetime.strptime(date, '%d.%m.%Y').date()
                in_time = time_in_range(period=3, date=date)

                files_id = ', '.join([data['file1'], data['file2'], data['file3']])
                report_type = data.get('type')

                report_id = await db.check_restaurant.add(
                    CheckDay(
                        add_date=add_date,
                        type=report_type,
                        point=point,
                        user_id=data.get('user_id'),
                        files_id=files_id,
                        in_time=in_time,
                        supervisor=supervisor.last_name if supervisor else None,
                    )
                )

                logging.info(
                    f'"{report_type}" {point} за {date} добавлен, отправил > {user.full_name}')

                caption = f'<b>{report_type}</b>\n' \
                          f'{pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=add_date)}\n' \
                          f'{"*" * 25}\n' \
                          f'Точка: <b>{point}</b>\n' \
                          f'Сотрудник: {user.full_name}\n' \
                          f'Проверен: Нет\n' \
                          f'#{report_type}_{point}'

                media = await media_create(files_id.split(', '), caption)
                await message.answer_media_group(media=media, allow_sending_without_reply=True)

                reply_markup = boss_report_menu if user_id in tg.BOSS else main_menu
                await message.answer('Отправили на проверку 👍', reply_markup=reply_markup)

                if supervisor:
                    supervisor_id = supervisor.user_id

                    kb = create_inline_kb(
                        btns={'✅ Подтвердить?': f'checkRestaurantReport_{report_id}'},
                    )

                    try:
                        await bot.send_media_group(supervisor_id, media=media, allow_sending_without_reply=True)
                        await bot.send_message(supervisor_id, 'После просмотра, нажми кнопку для подтверждения 👇',
                                               reply_markup=kb)
                        logging.info(
                            f'"{report_type}" {point} на проверке у {supervisor_id} {supervisor.full_name}, {dt_formatted()}')
                    except Exception as e:
                        logging.warning(f'{supervisor_id} {supervisor.full_name} > {e}')

                await state.clear()
            else:
                await state.set_state(RestaurantEvening.file4)
                await message.answer(check_q['ev_4'])
    else:
        await message.answer('Загрузи одно видео!!!')


@router.message(StateFilter(RestaurantEvening.file4), F.video | F.photo | F.document | F.text)
async def evening_file4(message: Message, state: FSMContext):
    if message.video:
        await state.update_data(file4=message.video.file_id)
        await state.set_state(RestaurantEvening.file5)
        await message.answer(check_q['ev_5'])
    else:
        await message.answer('Загрузи одно видео!!!')


@router.message(StateFilter(RestaurantEvening.file5), F.video | F.photo | F.document | F.text)
async def evening_file5(message: Message, state: FSMContext):
    if message.video:
        await state.update_data(file5=message.video.file_id)
        await state.set_state(RestaurantEvening.file6)
        await message.answer(check_q['ev_6'])
    else:
        await message.answer('Загрузи одно видео!!!')


@router.message(StateFilter(RestaurantEvening.file6), F.video | F.photo | F.document | F.text)
async def evening_file6(message: Message, state: FSMContext):
    if message.video:
        await state.update_data(file6=message.video.file_id)
        await state.set_state(RestaurantEvening.file7)
        await message.answer(check_q['ev_7'])
    else:
        await message.answer('Загрузи одно видео!!!')


@router.message(StateFilter(RestaurantEvening.file7), F.video | F.photo | F.document | F.text)
async def evening_file7(message: Message, state: FSMContext, db: Database):
    if message.video:

        user_id = message.from_user.id
        async with ChatActionSender.typing(chat_id=user_id, bot=bot):

            user = await db.user.get_one(user_id=user_id)
            await state.update_data(file7=message.video.file_id)

            data = await state.get_data()
            date = data.get('date')
            point = data.get('point')
            report_type = data.get('type')

            add_date = datetime.strptime(date, '%d.%m.%Y').date()
            in_time = time_in_range(period=3, date=date)

            supervisors = await db.user.get_supervisors()
            supervisor = next((sv for sv in supervisors if point in sv.points.split(', ')), None)

            files_id = ', '.join(
                [data['file1'], data['file2'], data['file3'], data['file4'], data['file5'], data['file6'],
                 data['file7']])

            report_id = await db.check_restaurant.add(
                CheckDay(
                    add_date=add_date,
                    type=report_type,
                    point=point,
                    user_id=data.get('user_id'),
                    files_id=files_id,
                    in_time=in_time,
                    supervisor=supervisor.last_name if supervisor else None,
                )
            )

            logging.info(f'"{report_type}" {report_id=} {point} за {add_date} добавлен, отправил > {user.full_name}')

            caption = f'<b>{report_type}</b>\n' \
                      f'{pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=add_date)}\n' \
                      f'{"*" * 25}\n' \
                      f'Точка: <b>{point}</b>\n' \
                      f'Сотрудник: {user.full_name}\n' \
                      f'Проверен: Нет\n' \
                      f'#{report_type.replace(" ", "_")}_{point}'

            logging.info("Сохраняем данные %s", await state.get_data())

            media = await media_create(data, caption)
            await message.answer_media_group(media=media, allow_sending_without_reply=True)

            reply_markup = boss_report_menu if user_id in tg.BOSS else main_menu
            await message.answer('Отправили на проверку 👍', reply_markup=reply_markup)

        if supervisor:
            supervisor_id = supervisor.user_id

            kb = create_inline_kb(
                btns={'✅ Подтвердить?': f'checkRestaurantReport_{report_id}'},
            )

            try:
                await bot.send_media_group(supervisor_id, media=media, allow_sending_without_reply=True)
                await bot.send_message(supervisor_id, 'После просмотра, нажми кнопку для подтверждения 👇',
                                       reply_markup=kb)
                logging.info(
                    f'"{report_type}" {point} на проверке у {supervisor_id} {supervisor.full_name}, {dt_formatted()}')
            except Exception as e:
                logging.warning(f'{supervisor_id} {supervisor.full_name} > {e}')

        await state.clear()

    else:
        await message.answer('Загрузи одно видео!!!')


@router.callback_query(F.data.startswith('checkRestaurantReport'), StateFilter(None))
async def check_report_start(callback_query: CallbackQuery, state: FSMContext, db: Database):
    """Сборка данных подтверждения проверки отчета"""
    await callback_query.answer()

    user_id = callback_query.from_user.id
    user = await db.user.get_one(user_id=user_id)
    if user.status:
        answer_data = callback_query.data
        report_id = int(answer_data.split('_')[1])
        await state.update_data(report_id=report_id)
        await state.set_state(CheckRestaurantReport.comment)
        await bot.send_message(user_id, 'Введи комментарий к отчету 👇', reply_markup=ok)
        await bot.delete_message(user_id, message_id=callback_query.message.message_id)
    else:
        await bot.delete_message(user_id, message_id=callback_query.message.message_id)
        await bot.send_message(user_id, 'Нет доступа', reply_markup=remove)


@router.message(StateFilter(CheckRestaurantReport.comment), F.text)
async def check_report_comment(message: Message, state: FSMContext, db: Database):
    user_id = message.from_user.id

    data = await state.get_data()
    report_id = data.get('report_id')
    comment = message.text

    report = await db.check_restaurant.get_by_id(report_id=report_id)

    time_diff_seconds = (
            get_current_datetime().replace(tzinfo=timezone.utc) -
            report.created_at.replace(tzinfo=timezone.utc)).total_seconds()

    seconds = time.gmtime(time_diff_seconds)
    duration_formatted = time.strftime("%H:%M:%S", seconds)
    duration = datetime.strptime(time.strftime("%H:%M:%S", seconds), "%H:%M:%S").time()

    await db.check_restaurant.update(
        report_id=report_id,
        comment=comment,
        verified=True,
        duration=duration
    )

    report_type = report.type
    point = report.point
    add_date = report.add_date

    logging.info(
        f'"{report_type}" {report_id=} {point} за {add_date}, проверен: {dt_formatted()} > {report.user.user_id} {report.user.full_name}')

    smile = '☀' if report_type in ['Утренний до 10', 'Утренний до 12'] else '🌘'
    msg = f'<b>{smile} {report_type} отчёт</b>\n' \
          f'{pytils.dt.ru_strftime(u"%d %B %y, %a", inflected=True, date=add_date)}\n' \
          f'{"*" * 25}\n' \
          f'Точка: <b>{point}</b>\n' \
          f'Комментарий: {comment}\n' \
          f'Проверен за: {duration_formatted} ч.\n' \
          f'#{report_type.replace(" ", "_")}_{point}'

    await message.answer('Подтвердили отчет 👍')

    supervisors = await db.user.get_supervisors()
    supervisor = next((sv for sv in supervisors if point in sv.points.split(', ')), None)

    if supervisor:
        try:
            await bot.send_message(supervisor.user_id, msg)
        except Exception as e:
            logging.warning(f'{supervisor.user_id} {supervisor.full_name} > {e}')

    if user_id in tg.BOSS:
        await message.answer('Еще вопросы? 👇', reply_markup=boss_main_menu)
    else:
        await message.answer('Еще вопросы? 👇', reply_markup=main_menu)

    if report_type in ['Утренний до 10', 'Утренний до 12'] or add_date != dt_formatted(6):
        user_ids = await google_exits_by_point(point=point, s_date=0, e_date=1)
    else:
        user_ids = await google_exits_by_point(point=point)

    check = []
    if user_ids:
        for user in user_ids:
            try:
                if user not in (supervisor.user_id for supervisor in supervisors) and user not in check:
                    check.append(user)
                    await bot.send_message(user, msg)
            except Exception as e:
                logging.warning('Check report comment schedule: %s > %s', user, e)
                continue

    logging.info(f'{user_ids=} {check=}')

    await send_other_staff(message, msg=msg, check=check)
    await state.clear()


async def send_other_staff(message: Message, media=None, photo=None, msg=None, check=None):
    """Отправка наблюдателям"""
    for user_id in tg.OBSERVERS:
        if message.from_user.id == user_id:
            continue
        try:
            if media:
                await bot.send_media_group(user_id, media=media, allow_sending_without_reply=True)
            elif msg:
                if photo:
                    await bot.send_photo(user_id, photo=photo, caption=msg, allow_sending_without_reply=True)
                elif not photo and user_id not in check:
                    await bot.send_message(user_id, msg)
        except Exception as e:
            logging.warning('user_id: %s > %s', user_id, e)
