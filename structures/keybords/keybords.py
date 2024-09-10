#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Union, List

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from sqlalchemy.ext.asyncio import AsyncSession

from database import async_engine, Database

from structures.keybords.cb_makers import create_kb
from structures.keybords.keybords_list import *
from structures.role import Role
from utils.utils import subsets_combinations

boss_main_menu = create_kb(btns=boss_main_m)

boss_staff_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            *(KeyboardButton(text=text) for text in boss_staff_m[0])
        ],
        [
            *(KeyboardButton(text=text) for text in boss_staff_m[1])
        ],
        [
            *(KeyboardButton(text=text) for text in boss_staff_m[2])
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

boss_report_menu = create_kb(btns=boss_report_m)
boss_payments_category_menu = create_kb(btns=boss_payments_category_m)
boss_category_menu = create_kb(btns=boss_category_m)
boss_payments_menu = create_kb(btns=boss_payments_m)
boss_projects_works_menu = create_kb(btns=boss_projects_works_m)
boss_projects_expenses_menu = create_kb(btns=boss_projects_expenses_m)
boss_home_works_menu = create_kb(btns=boss_home_works_m)
boss_home_expenses_menu = create_kb(btns=boss_home_expenses_m)
boss_other_menu = create_kb(btns=boss_other_m)
main_menu = create_kb(btns=staff_main_m)
grind_type_menu = create_kb(btns=grind_type_m)
morning_type_menu = create_kb(btns=morning_type_m)
no_check = create_kb(btns=('Без чека',))
no_comment = create_kb(btns=('Нет', '❌ Отмена'), input_field_placeholder='Комментарий...')


# точки
async def get_points() -> List[str]:
    points_all = await get_points_all()
    return [p for p in points_all if 'Офис' not in p]


# точки все
async def get_points_all(not_in: tuple = ('Тест',)) -> List[str]:
    async with AsyncSession(async_engine) as session:
        points = await Database(session).point.get_all()
        return [
            p.name
            for point in points
            for p in [point] if p.name not in not_in
        ]


async def points_menu() -> ReplyKeyboardMarkup:
    return create_kb(btns=(*await get_points(), '❌ Отмена'), sizes=(1,))


async def points_menu_all() -> ReplyKeyboardMarkup:
    return create_kb(btns=(*sorted(await get_points_all()), '❌ Отмена'), sizes=(1,))


async def employee_menu(active: bool = True, check: bool = False) -> Union[tuple, ReplyKeyboardMarkup]:
    async with AsyncSession(async_engine) as session:
        users = await Database(session).user.get_all()

    if active:
        staff = (
            user.full_name
            for user in users if user.status
        )
    else:
        staff = (
            user.full_name
            for user in users
        )

    if check:
        return tuple(staff)

    return create_kb(btns=(*sorted(tuple(staff)), '❌ Отмена'), sizes=(1,))


async def points_menu_sv() -> ReplyKeyboardMarkup:
    return create_kb(btns=(*subsets_combinations(await get_points_all(('Тест', 'Офис'))), '❌ Отмена'), sizes=(1,))


points_sv_menu = create_kb(
    btns=(
        'Балашиха, Железнодорожный',
        'Балашиха, Ногинск',
        'Балашиха, Ногинск 2',
        'Балашиха, Электросталь',
        'Ногинск, Электросталь',
        'Ногинск 2, Электросталь',
        'Железнодорожный, Ногинск',
        'Железнодорожный, Ногинск 2',
        'Железнодорожный, Электросталь',
        'Балашиха, Железнодорожный, Ногинск, Электросталь',
        'Балашиха, Железнодорожный, Ногинск, Ногинск 2, Электросталь',
        'Не супервайзер',
        '❌ Отмена'
    ), sizes=(1,))

positions = create_kb(btns=(*company_positions, '❌ Отмена'), sizes=(1,))

role_menu = create_kb(btns=(*Role.values(), '❌ Отмена'), sizes=(1,))

yes_no_cancel = create_kb(btns=('Да', 'Нет', '❌ Отмена'))
yes_no = create_kb(btns=('Да', 'Нет'))
all_ok = create_kb(btns=('Все ОК', '❌ Отмена'))
ok = create_kb(btns=('Все ОК',), input_field_placeholder='Комментарий...')
no = create_kb(btns=('Нет',), input_field_placeholder='Комментарий...')

safe_menu = create_kb(btns=safe_m)
cancel_menu = create_kb(btns=('❌ Отмена',), input_field_placeholder='Комментарий...')

q1_a = create_kb(btns=('Да', 'Закончились ингредиенты', 'Не используем', '❌ Отмена'))
write_off_menu = create_kb(btns=(*write_off_reasons, '❌ Отмена'))

location = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='📍 Отправить локацию', request_location=True)
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

remove = ReplyKeyboardRemove()
