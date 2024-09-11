from aiogram import Router, F
from aiogram.filters import Command, and_f, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.models import Point
from filters.filters import AdminFilter, ChatTypeFilter

from structures.keybords import (
    boss_other_menu,
    points_menu_all,
    remove,
)

from fsm.points import PointAdd, PointDelete, PointUpdate

from database import Database
from core.config import settings, GoogleSheetsSettings

gs: GoogleSheetsSettings = settings.gs

router = Router(name=__name__)
router.message.filter(and_f(AdminFilter(), ChatTypeFilter(['private'])))

statesPoints = StateFilter(
    PointAdd(),
    PointDelete(),
    PointUpdate(),
)


@router.message(Command("cancel"), statesPoints)
@router.message(F.text.lower().in_({'отмена', 'отменить', '❌ отмена', '⬆ выйти', 'cancel'}), statesPoints)
async def cancel_points_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    answer_text, reply_markup = ('Еще вопросы? 👇', boss_other_menu)
    await message.answer(answer_text, disable_web_page_preview=True, reply_markup=reply_markup)


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
    await message.answer('Введи алиас (3 символа, например: Балашиха > b) 👇', reply_markup=remove)


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
