import logging
import random

from aiogram import Router, F
from aiogram.filters import Command, and_f, StateFilter
from aiogram.types import (Message, CallbackQuery)
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender

from filters.filters import AdminFilter, ChatTypeFilter

from structures.keybords import (
    main_menu,
    boss_staff_menu,
    points_menu_all,
    remove,
    employee_menu,
    cancel_menu,
    positions,
    no,
    points_menu_sv,
    role_menu,
    boss_main_menu
)

from fsm.employee import (
    EmployeeAdd,
    EmployeeDelete,
    EmployeeUpdate,
    EmployeeActivate,
)

from core.bot import bot
from database import User, Database
from structures.role import Role
from structures.restrictions import Restrictions as Rest
from utils.utils import divide_list
from services.async_google_service import (google_exits, google_add_row, google_update_row)
from core.config import settings, GoogleSheetsSettings

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
async def cancel_employee_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    answer_text, reply_markup = ('Еще вопросы? 👇', boss_staff_menu)
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
            f'{"*" * 25}\n'
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
            f'{"*" * 25}\n'
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
        f'{"*" * 25}\n'
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
            f'{"*" * 25}\n'
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
        f'{"*" * 25}\n'
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
