import logging
import os
import re
import decimal

import aiofiles
import pprintpp as pp
from typing import Union

from aiocsv import AsyncWriter
from aiogram import Router, F
from aiogram.filters import Command, or_f
from aiogram.filters import StateFilter
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy.ext.asyncio import AsyncSession

from common.questions import sheets
from core.bot import bot

from core.config import settings, TgBot, GoogleSheetsSettings
from database import async_engine, WriteOff, Product, Database
from database.tabels import truncate_table

from filters.filters import ChatTypeFilter

from structures.keybords import (
    points_menu,
    remove,
    write_off_menu,
    no,
    boss_other_menu,
    main_menu,
    boss_main_menu,
    get_points_all,
    grind_type_menu,
    cancel_menu,
    create_kb,
    create_inline_kb,
    yes_no,
)
from structures.keybords.keybords_list import write_off_reasons
from structures.fsm.write_off import WriteOffAdd, WriteOffSend, GrindSetting

from services.async_google_service import (
    google_save_file,
    google_get_all_records,
    google_add_row,
    google_clear_folder,
    google_write_off,
)

from services.path import create_dir, clear_dir, create_src
from structures.role import Role
from utils.utils import includes_number, get_current_datetime

pp = pp.PrettyPrinter(indent=4)

tg: TgBot = settings.bot
gs: GoogleSheetsSettings = settings.gs

router = Router(name=__name__)
router.message.filter(ChatTypeFilter(['private']))


states = StateFilter(
    WriteOffAdd(),
    GrindSetting(),
    WriteOffSend()
)


@router.message(Command("cancel"), states)
@router.message(F.text.lower().in_({'отмена', 'отменить', '❌ отмена', '⬆ выйти', 'cancel'}), states)
async def cancel_write_off_handler(message: Message, state: FSMContext, db: Database) -> None:
    await state.clear()
    user_role_reply_markup = {
        Role.admin: ('Еще вопросы? 👇', boss_main_menu),
        Role.staff: ('Еще вопросы? 👇', main_menu),
        Role.supervisor: ('Еще вопросы? 👇', main_menu)
    }

    user_id = message.from_user.id
    user_role = await db.user.get_role(user_id=user_id)
    answer_text, reply_markup = user_role_reply_markup.get(user_role)
    await message.answer(answer_text, disable_web_page_preview=True, reply_markup=reply_markup)


async def load_codes() -> Union[None, str]:
    """Загрузка `кодов` товаров в БД(codes)"""
    products = await google_get_all_records(gs.BOOK_WRITE_OFF_ID, gs.SHEET_CODES)
    if len(products) > 0:
        async with AsyncSession(async_engine) as session:

            await truncate_table(Product)
            products_list = [
                Product(**{k: decimal.Decimal(str(v).replace(' ', ',')) if k == 'price' else v for k, v in p.items()})
                for p in products]
            await Database(session).product.add_all(products=products_list)

            # for product in products:
            #     try:
            #         product['price'] = decimal.Decimal(str(product['price']).replace(' ', ','))
            #         await Database(session).product.add(Product(**product))
            #     except decimal.ConversionSyntax:
            #         logging.warning("Invalid price value: %s", product.get("price"))
            #         continue
    else:
        return 'Нет данных для добавления 🤷‍♂'


@router.message(StateFilter(None), F.text.lower().in_(['♻ списать', 'списание', 'списать']))
async def write_off_start(message: Message, state: FSMContext, db: Database):
    user_id = message.from_user.id
    user = await db.user.get_one(user_id=user_id)
    if not user:
        await state.clear()
        return await message.answer(f'Пользователя {user_id} нет в базе, добавьте себя, назначьте права!!!')

    await state.update_data(user_id=user.id)
    await state.set_state(WriteOffAdd.POINT)
    await message.reply('Выбери точку 👇', reply_markup=await points_menu())


@router.message(StateFilter(WriteOffAdd.POINT), F.text)
async def write_off_point(message: Message, state: FSMContext, db: Database):
    if await db.point.get_one(name=message.text):

        await state.update_data(point=message.text)
        await state.set_state(WriteOffAdd.CATEGORY)

        categories = await db.product.category()
        categories_menu = create_kb(categories, sizes=(1,))
        await message.answer('Выбери категорию 👇', reply_markup=categories_menu)

    else:
        await message.answer('Похоже ты ошибся, выбери точку 👇', reply_markup=await points_menu())


@router.message(StateFilter(WriteOffAdd.CATEGORY), F.text)
async def write_off_category(message: Message, state: FSMContext, db: Database):
    categories = await db.product.category()

    if message.text in categories:
        await state.set_state(WriteOffAdd.CODE)

        products = await db.product.get_all_by_category(category=message.text)
        _ = {f'{product.code}, {product.product} ({product.unit})': f'productCode_{product.code}' for product in
             products}
        products_menu = create_inline_kb(btns=_, sizes=(1,))

        await message.answer('Выбери товар 👇', reply_markup=products_menu)

    else:
        await state.set_state(WriteOffAdd.CATEGORY)
        categories_menu = create_kb(categories, sizes=(1,))
        await message.answer('Похоже ты ошибся, выбери категорию 👇', reply_markup=categories_menu)


@router.callback_query(F.data.startswith('product'), StateFilter(WriteOffAdd.CODE))
async def write_off_code(callback_query: CallbackQuery, state: FSMContext, db: Database):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    callback_data, code = callback_query.data.split('_')
    if callback_data == 'productCode':
        if includes_number(code):
            product = await db.product.get_one(code=int(code))

            if product:
                await state.update_data(code=product.code)
                await state.set_state(WriteOffAdd.QUANTITY)
                await callback_query.message.edit_text(
                    f'Введи количество для списания:\n<b>{product.code}, {product.product} ({product.unit})</b> 👇\n\n'
                    f'<i>🔸 Штучный товар в штуках;\n'
                    f'🔸 Весовой - фактический вес (500 гр. или мл. = 0.5)\n\n'
                    f'Без ед. измерения (кг, гр, мг, л, мл...)</i>', reply_markup=None)
        else:
            await state.set_state(WriteOffAdd.CATEGORY)
            categories = await db.product.category()
            categories_menu = create_kb(categories, sizes=(1,))
            await bot.delete_message(user_id, message_id=callback_query.message.message_id)
            await bot.send_message(user_id, 'Похоже ты ошибся, выбери категорию 👇',
                                   reply_markup=categories_menu)


@router.message(StateFilter(WriteOffAdd.QUANTITY), F.text)
async def write_off_quantity(message: Message, state: FSMContext):
    if includes_number(message.text):
        await state.update_data(quantity=float(re.sub(r'[^\d\.]', '', message.text.replace(',', '.'))))
        await state.set_state(WriteOffAdd.REASON)
        await message.answer('Выбери причину списания 👇', reply_markup=write_off_menu)
    else:
        await message.answer(
            f'Похоже ты ошибся!!!\n'
            f'Введи кол-во для списания👇\n\n'
            f'<i>🔸 Штучный товар в штуках;\n'
            f'🔸 Весовой - фактический вес (500 гр. или мл. = 0.5)\n\n'
            f'Без ед. измерения (кг, гр, мг, л, мл...)</i>'
        )


@router.message(StateFilter(WriteOffAdd.REASON), F.text)
async def write_off_reason(message: Message, state: FSMContext):
    if message.text in write_off_reasons:
        await state.update_data(reason=message.text)
        await state.set_state(WriteOffAdd.COMMENT)
        await message.answer('Добавь комментарий к списанию 👇', reply_markup=no)
    else:
        await message.answer('Похоже ты ошибся, выбери причину списания 👇', reply_markup=write_off_menu)


@router.message(StateFilter(WriteOffAdd.COMMENT), F.text)
async def write_off_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await state.set_state(WriteOffAdd.FILE)
    await message.answer('Добавь одно фото 👇', reply_markup=remove)


@router.message(StateFilter(WriteOffAdd.FILE), F.photo)
async def write_off_file(message: Message, state: FSMContext, db: Database):
    user_id = message.from_user.id
    async with ChatActionSender.typing(chat_id=user_id, bot=bot):

        user = await db.user.get_one(user_id=user_id)
        await state.update_data(file=message.photo[-1].file_id)
        d = await state.get_data()

        src, date_time, product = await _get_src(message, d, db=db)
        name = f'{d["point"]}_{date_time.strftime("%d_%m_%y %H_%M_%S")}_code_{d["code"]}'

        file_id = await google_save_file(name=name, file_path=src)

        expense_company = 'Списание без МОЛ' if d['reason'] == 'Реклама' else None

        if d['point'] in sheets:
            await google_add_row(gs.BOOK_WRITE_OFF_ID, sheets[d['point']],
                                 [date_time.strftime('%Y-%m-%d %H:%M:%S'),
                                  user_id,
                                  user.full_name,
                                  d['code'],
                                  '',
                                  d['quantity'],
                                  d['reason'],
                                  d['comment'],
                                  f'https://drive.google.com/file/d/{file_id}/view?usp=drivesdk',
                                  f'=IMAGE("https://drive.google.com/uc?export=view&id={file_id}";2)',
                                  expense_company])

        # TODO product.product в product.name
        clear_dir(user_id)
        msg = (f'<b>⚠ Новое списание</b>\n'
               f'{"*" * 25}\n'
               f'Точка: <b>{d["point"]}</b>\n'
               f'Сотрудник: {user.full_name}\n'
               f'Товар: {d["code"]}, {product.product}\n'
               f'Кол-во: {d["quantity"]}\n'
               f'Причина: {d["reason"]}\n'
               f'Комментарий: {d["comment"]}\n'
               f'<a href="https://drive.google.com/uc?export=view&id={file_id}">Фото</a>\n'
               f'<a href="https://clck.ru/Vsj5h">Файл списания</a>\n'
               f'#Списание')

        await message.delete()
        if user_id in tg.BOSS:
            await message.answer(msg, reply_markup=remove)
        else:
            await message.answer(msg, reply_markup=remove)

    # TODO product.product в product.name
    await _send_sv(message, point=d["point"], msg=msg, db=db)
    await _send_other(message, msg=msg)

    await state.set_state(WriteOffAdd.NEXT)
    await message.answer(f'Запишем еще?', reply_markup=yes_no)

    # await state.clear()


@router.message(StateFilter(WriteOffAdd.NEXT), F.text)
async def write_off_end(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text == 'Да':
        await state.clear()
        await state.set_state(WriteOffAdd.POINT)
        await bot.delete_message(user_id, message.message_id - 1)
        await message.answer('Выбери точку 👇', reply_markup=await points_menu())
    elif message.text == 'Нет':
        await state.clear()
        if user_id in tg.BOSS:
            await message.answer('Меню 👇', reply_markup=boss_other_menu)
        else:
            await message.answer('Меню 👇', reply_markup=main_menu)

    else:
        await state.set_state(WriteOffAdd.NEXT)
        await message.answer(f'Запишем еще?', reply_markup=yes_no)


@router.message(StateFilter(WriteOffAdd.FILE))
async def write_off_upload_file(message: Message, ):
    await bot.delete_message(message.from_user.id, message.message_id - 1)
    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.send_message(message.from_user.id, 'Загрузи одно фото!!!')


@router.message(StateFilter(None), F.text.lower() == '☕ эспрессо')
async def grind_setting_start(message: Message, state: FSMContext, db: Database):
    """Старт для добавления списания по настройке помола кофемашины"""
    user_id = message.from_user.id
    user = await db.user.get_one(user_id=user_id)
    if not user:
        await state.clear()
        return await message.answer(f'Пользователь {user_id} нет в базе, добавьте себя, назначьте права!!!')

    await state.update_data(user_id=user.id)

    await state.set_state(GrindSetting.TYPE)
    await message.reply('Выбери 👇', reply_markup=grind_type_menu)


@router.message(StateFilter(GrindSetting.TYPE), F.text)
async def grind_setting_type(message: Message, state: FSMContext):
    if message.text in ['Настройка', 'Конец смены']:
        await state.update_data(type=message.text)
        await state.set_state(GrindSetting.POINT)
        await message.reply('Выбери точку 👇', reply_markup=await points_menu())
    else:
        await message.reply('Выбери 👇', reply_markup=grind_type_menu)


@router.message(StateFilter(GrindSetting.POINT), F.text)
async def grind_setting_point(message: Message, state: FSMContext, db: Database):
    if await db.point.get_one(name=message.text):
        user_id = message.from_user.id
        await state.update_data(point=message.text)
        data = await state.get_data()
        grind_type = data.get('type')

        if grind_type == 'Настройка':

            await state.update_data(code=2099, reason="Порча", comment="Настройка эспрессо до 3 шт")
            data = await state.get_data()

            count = await db.write_off.limit_setting_coffee_query(point=data['point'], comment=data['comment'])

            if count and count >= 3:
                msg = 'Max 3 настройки за смену!!!\nНеобходимо провести > 3, используй кнопку <b>♻ Списать</b>'
                if user_id in tg.BOSS:
                    await message.answer(msg, reply_markup=boss_other_menu)
                else:
                    await message.answer(msg, reply_markup=main_menu)
                await state.clear()
            else:
                await state.set_state(GrindSetting.QUANTITY)
                await message.answer(
                    f'Введи кол-во для списания 👇\n\n'
                    f'<b>Эспрессо ДВОЙНОЙ 60мл.</b> - 1 настройка\n\n'
                    f'<i>Max 3 настройки за смену!!!</i>', reply_markup=remove)

        elif grind_type == 'Конец смены':

            await state.update_data(code=2098, reason="Порча", comment="Настройка эспрессо конец смены", quantity=1)
            data = await state.get_data()

            count = await db.write_off.limit_setting_coffee_query(point=data['point'], comment=data['comment'])

            if count and count >= 1:
                msg = 'Max 1 списание за смену!!!\nНеобходимо > 1, используй кнопку <b>♻ Списать</b>'
                if user_id in tg.BOSS:
                    await message.answer(msg, reply_markup=boss_other_menu)
                else:
                    await message.answer(msg, reply_markup=main_menu)
                await state.clear()
            else:
                await state.set_state(GrindSetting.FILE)
                await message.answer('Добавь одно фото 👇', reply_markup=remove)
    else:
        await message.answer('Похоже ты ошибся, выбери точку 👇', reply_markup=await points_menu())


@router.message(StateFilter(GrindSetting.QUANTITY), F.text)
async def grind_setting_quantity(message: Message, state: FSMContext, db: Database):
    if includes_number(message.text):
        quantity = int(re.sub(r'[^\d\.]', '', message.text.replace(',', '.')))
        await state.update_data(quantity=quantity)

        if quantity <= 3:
            data = await state.get_data()
            day_count = await db.write_off.limit_setting_coffee_query(point=data['point'], comment=data['comment'])
            if day_count and day_count + quantity > 3:
                msg = f'Max 3 настройки за смену!!!\n' \
                      f'Уже списано: {day_count}\n' \
                      f'Необходимо провести > 3, используй кнопку <b>♻ Списать</b>\n' \
                      f'Введи кол-во для списания 👇'

                await message.answer(msg, reply_markup=cancel_menu)
            else:
                await state.set_state(GrindSetting.FILE)
                await message.answer(f'Добавь одно видео, не больше 20МБ 👇\n'
                                     f'<i>На видео непригодный эспрессо должен быть утилизирован (вылит).</i>')
        else:
            await message.answer(
                f'Max 3 настройки за смену!!!\n'
                f'Необходимо провести > 3, используй кнопку <b>♻ Списать</b>\n'
                f'Введи кол-во для списания 👇')
    else:
        await message.answer(f'Похоже ты ошибся!!!\nВведи кол-во для списания 👇')


@router.message(StateFilter(GrindSetting.FILE), F.photo | F.video)
async def grind_setting_file(message: Message, state: FSMContext, db: Database):
    user_id = message.from_user.id

    async with ChatActionSender.typing(chat_id=user_id, bot=bot):

        user = await db.user.get_one(user_id=user_id)
        expense_company = 'Списание без МОЛ'
        state_data = await state.get_data()

        if state_data['type'] == 'Настройка':
            if message.video:

                await state.update_data(file=message.video.file_id)
                d = await state.get_data()

                src, date_time, product = await _get_src(message, d, dir_type="video", db=db)
                name = f'{d["point"]}_{date_time.strftime("%d_%m_%y %H_%M_%S")}_setting_coffee_machine'

                file_id = await google_save_file(name=name, file_path=src, mime_type='video/mp4')

                if d['point'] in sheets:
                    await google_add_row(
                        gs.BOOK_WRITE_OFF_ID,
                        sheets[d['point']],
                        [date_time.strftime('%Y-%m-%d %H:%M:%S'),
                         user_id,
                         user.full_name,
                         d['code'],
                         '',
                         d['quantity'],
                         d['reason'],
                         d['comment'],
                         f'https://drive.google.com/file/d/{file_id}/view?usp=drivesdk',
                         '',
                         expense_company]
                    )

                clear_dir(user_id, dir_type="video")
                msg = f'Добавили списание 👍\n' \
                      f'{"*" * 25}\n' \
                      f'Точка: <b>{d["point"]}</b>\n' \
                      f'Сотрудник: {user.full_name}\n' \
                      f'Товар: {product.product}\n' \
                      f'Кол-во: {d["quantity"]}\n' \
                      f'Причина: {d["comment"]}\n' \
                      f'#НастройкаПомола'

                if user_id in tg.BOSS:
                    await message.answer(msg, reply_markup=boss_other_menu)
                else:
                    await message.answer(msg, reply_markup=main_menu)

                await _send_sv(
                    message,
                    point=d["point"],
                    msg=f'<b>⚠ Новое списание</b>\n'
                        f'{"*" * 25}\n'
                        f'Точка: <b>{d["point"]}</b>\n'
                        f'Сотрудник: {user.full_name}\n'
                        f'Товар: {product.product}\n'
                        f'Кол-во: {d["quantity"]}\n'
                        f'Причина: {d["comment"]}\n'
                        f'<a href="https://drive.google.com/uc?export=view&id='
                        f'{file_id}">Фото</a>\n'
                        f'<a href="https://clck.ru/Vsj5h">Файл списания</a>\n'
                        f'#НастройкаПомола',
                    db=db
                )
                await _send_other(message, msg=msg)
                await state.clear()
            else:
                await bot.delete_message(message.from_user.id, message.message_id - 1)
                await bot.delete_message(message.from_user.id, message.message_id)
                await bot.send_message(message.from_user.id,
                                       f'Добавь одно видео, не больше 20МБ 👇\n'
                                       f'На видео непригодный эспрессо должен быть утилизирован (вылит).')

        elif state_data['type'] == 'Конец смены':
            if message.photo:

                await state.update_data(file=message.photo[-1].file_id)
                d = await state.get_data()

                src, date_time, product = await _get_src(message, await state.get_data(), db=db)
                name = f'{d["point"]}_{date_time.strftime("%d_%m_%y %H_%M_%S")}_setting_coffee_machine'

                file_id = await google_save_file(name=name, file_path=src)

                if d['point'] in sheets:
                    await google_add_row(
                        gs.BOOK_WRITE_OFF_ID,
                        sheets[d['point']],
                        [date_time.strftime('%Y-%m-%d %H:%M:%S'),
                         user_id,
                         user.full_name,
                         d['code'],
                         '',
                         d['quantity'],
                         d['reason'],
                         d['comment'],
                         f'https://drive.google.com/file/d/{file_id}/view?usp=drivesdk',
                         f'=IMAGE("https://drive.google.com/uc?export=view&id={file_id}";2)',
                         expense_company]
                    )

                clear_dir(user_id)
                msg = f'Добавили списание 👍\n' \
                      f'{"*" * 25}\n' \
                      f'Точка: <b>{d["point"]}</b>\n' \
                      f'Сотрудник: {user.full_name}\n' \
                      f'Товар: {product.product}\n' \
                      f'Кол-во: {d["quantity"]}\n' \
                      f'Причина: {d["comment"]}\n' \
                      f'#НастройкаПомола'

                if user_id in tg.BOSS:
                    await message.answer(msg, reply_markup=boss_other_menu)
                else:
                    await message.answer(msg, reply_markup=main_menu)

                await _send_sv(
                    message,
                    point=d["point"],
                    msg=f'<b>⚠ Новое списание</b>\n'
                        f'{"*" * 25}\n'
                        f'Точка: <b>{d["point"]}</b>\n'
                        f'Сотрудник: {user.full_name}\n'
                        f'Товар: {product.product}\n'
                        f'Кол-во: {d["quantity"]}\n'
                        f'Причина: {d["comment"]}\n'
                        f'<a href="https://drive.google.com/uc?export=view&id='
                        f'{file_id}">Видео</a>\n'
                        f'<a href="https://clck.ru/Vsj5h">Файл списания</a>\n'
                        f'#НастройкаПомола',
                    db=db
                )
                await _send_other(message, msg=msg)
                await state.clear()
            else:
                await bot.delete_message(message.from_user.id, message.message_id - 1)
                await bot.delete_message(message.from_user.id, message.message_id)
                await bot.send_message(message.from_user.id, 'Загрузи одно фото!!!')


async def _send_sv(message: Message, point: str, msg: str, db: Database):
    """Отправка супервайзеру"""
    sv_id = None
    supervisors = await db.user.get_supervisors()

    for sv in supervisors:
        try:
            sv_id = sv.user_id
            if message.from_user.id != sv_id and sv.points and point in sv.points.split(', '):
                await bot.send_message(sv_id, text=msg)
        except Exception as e:
            logging.warning(f'Supervisor: %s > %s', sv_id, e, exc_info=True)
            continue


async def _send_other(message, msg):
    """Отправка наблюдателям"""
    for user_id in tg.OBSERVERS:
        try:
            if message.from_user.id != user_id and msg:
                await bot.send_message(user_id, msg)
        except Exception as e:
            logging.warning(f'User: %s > %s', user_id, e, exc_info=True)
            continue


async def _get_src(message: Message, state: dict, db: Database, dir_type: str = None):
    """Вспомогательная функция"""
    create_dir(message.from_user.id, dir_type=dir_type) if dir_type == "video" else create_dir(message.from_user.id)
    file_info = await bot.get_file(message.video.file_id) if dir_type == "video" else await bot.get_file(
        message.photo[len(message.photo) - 1].file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    src = create_src(message.from_user.id, file_info.file_path)
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file.getvalue())

    date_time = get_current_datetime()
    logging.info("State: %s", state)

    write_off = WriteOff(**state)
    await db.write_off.add(write_off)
    code = state["code"]
    product = await db.product.get_one(code)

    return src, date_time, product


@router.message(StateFilter(None), F.text.lower() == '📩 списания')
async def write_off_send_start(message: Message, state: FSMContext):
    """Старт отправки файла списания"""
    await state.set_state(WriteOffSend.POINT)
    await message.reply('Выбери точку 👇', reply_markup=await points_menu())


@router.message(StateFilter(WriteOffSend.POINT), F.text)
async def write_off_send_end(message: Message, state: FSMContext):
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        if message.text in await get_points_all():

            point = message.text

            cols = ['Дата', 'Сотрудник', 'Код товара', 'Наименование', 'Кол-во', 'Основание', 'Комментарий',
                    'Ссылка на фото', 'Статус']

            data = await google_write_off(sheets[point], cols)
            create_dir(dir_type='report')
            file_path = f'{os.getcwd()}/src/reports/{sheets[point]}.csv'

            async with aiofiles.open(file_path, mode='w', encoding='cp1251', newline='', errors='replace') as file:
                writer = AsyncWriter(file, delimiter=';')
                await writer.writerow(cols)
                await writer.writerows(data)

            await message.reply_document(FSInputFile(file_path, filename=f'{sheets[point]}.csv'),
                                         reply_markup=boss_other_menu)
            clear_dir(dir_type='report')
            await state.clear()
        else:
            await message.answer('Похоже ты ошибся, выбери точку 👇', reply_markup=await points_menu())


@router.message(F.text.lower() == '🔄 коды списаний')
async def update_codes_base(message: Message):
    """Обновляет базу кодов товаров"""
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        msg = await load_codes()
        if msg:
            await message.answer(msg, reply_markup=boss_other_menu)
        else:
            await message.answer('Базу кодов обновили 😁', reply_markup=boss_other_menu)


@router.message(F.text.lower() == '🆑 удалить фото')
async def clear_folder(message: Message):
    """Очистить папку с фотографиями списаний"""
    async with ChatActionSender.typing(chat_id=message.from_user.id, bot=bot):
        await google_clear_folder(gs.FOLDER_ID_PHOTO_SAVE)
        await message.answer('Очистили папку списаний', reply_markup=boss_other_menu)


@router.message(or_f(Command("cancel"), (F.text.lower().in_({'отмена', 'отменить', '❌ отмена', '⬆ выйти'}))))
async def cancel(message: Message, state: FSMContext, db: Database):
    """Отмена действия и выход из состояния"""

    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()

    user_role_reply_markup = {
        Role.admin: ('Еще вопросы? 👇', boss_main_menu),
        Role.staff: ('Еще вопросы? 👇', main_menu),
        Role.supervisor: ('Еще вопросы? 👇', main_menu)
    }

    user_id = message.from_user.id
    user_role = await db.user.get_role(user_id=user_id)
    answer_text, reply_markup = user_role_reply_markup.get(user_role)
    await message.answer(answer_text, disable_web_page_preview=True, reply_markup=reply_markup)


@router.message()
async def empty(message: Message, db: Database):
    """Не понятные сообщения"""

    text = message.text

    user_role_reply_markup = {
        Role.admin: boss_main_menu,
        Role.staff: main_menu,
        Role.supervisor: main_menu
    }

    user_id = message.from_user.id
    user_role = await db.user.get_role(user_id=user_id)
    reply_markup = user_role_reply_markup.get(user_role)
    answer_text = f'{text}\nЧто за ересь??? 🤣\nУчи матчасть >>> /help'
    await message.answer(answer_text, disable_web_page_preview=True, reply_markup=reply_markup)
