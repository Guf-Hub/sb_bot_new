# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from itertools import combinations
from typing import Union, List
import os
import shutil
from datetime import datetime, timedelta

import aiofiles
import pytz
from aiocsv import AsyncWriter

from aiogram.types import Message

from core.config import settings


def get_current_datetime(days: int = 0, hours: int = 0, minutes: int = 0, tz: str = "Europe/Moscow") -> datetime:
    """Возвращает сегодняшний datetime с учётом временной зоны Мск."""
    delta = timedelta(days=days, hours=hours, minutes=minutes)
    tz = pytz.timezone(tz)
    now = datetime.now(tz) + delta
    return now


def dt_formatted(str_type: int = None, minus_days: int = 0, plus_days: int = 0) -> str:
    """Возвращает сегодняшнюю дату строкой"""
    if str_type == 1:
        ft = '%d.%m.%Y'
    elif str_type == 2:
        ft = '%Y-%m-%d %H:%M:%S'
    elif str_type == 3:
        ft = '%d_%m_%Y'
    elif str_type == 4:
        ft = '%H:%M:%S'
    elif str_type == 5:
        ft = '%H'
    elif str_type == 6:
        ft = '%Y-%m-%d'
    elif str_type == 7:
        ft = '%d_%m_%y'
    else:
        ft = '%d.%m.%Y %H:%M:%S'

    return (get_current_datetime() - timedelta(days=minus_days) + timedelta(days=plus_days)).strftime(ft)


def to_datetime(date_string: str, date_format: str = '%Y-%m-%d %H:%M:%S'):
    return datetime.strptime(date_string, date_format)


def seconds_to_time(seconds: int, time_format: str = 'short') -> str:
    """Конвертация секунд в `ЧЧ:ММ:СС`

    :param seconds: количество секунд
    :param time_format: 'long' "%02d:%02d:%02d", 'short' "%02d:%02d"
    """
    seconds = seconds % (24 * 3600)
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    if time_format == 'long':
        return "%02d:%02d:%02d" % (hours, minutes, seconds)
    if time_format == 'short':
        return "%02d:%02d" % (hours, minutes)


def time_in_range(period: int = None, date: str = None):
    """Текущее время в диапазоне [start, end]"""
    import datetime
    current = get_current_datetime().time()

    if period == 1:
        start = datetime.time(9, 0, 0)
        end = datetime.time(10, 00, 0)
        return start <= current <= end

    if period == 2:
        start = datetime.time(9, 0, 0)
        end = datetime.time(12, 00, 0)
        return start <= current <= end

    if period == 3:
        if dt_formatted(1) == date:
            start = datetime.time(22, 0, 0)
            end = datetime.time(23, 59, 59)
            return start <= current <= end
        elif dt_formatted(1, minus_days=1) == date:
            end = datetime.time(3, 00, 0)
            return current <= end
        else:
            return False
    else:
        return False


async def write_report_csv(directory: str, headers: list, data: list, city: str, cur_time: datetime):
    """Асинхронное создание файла csv"""
    async with aiofiles.open(f'{directory}/{city}_{cur_time}.csv', 'w') as file:
        writer = AsyncWriter(file)
        if headers:
            await writer.writerow(headers)
        await writer.writerows(data)
    return f'{directory}/{city}_{cur_time}.csv'


def create_directory(file_path: str) -> None:
    """Функция для создания директории file_path: str путь до файла"""
    if not os.path.exists(file_path):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
        try:
            os.makedirs(path)
        except Exception as e:
            logging.warning(f'{path} > {e}')


def clear_directory(file_path: str) -> None:
    """Функция удаляющая данные из папки file_path: str путь до файла"""
    if os.path.exists(file_path):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
        try:
            shutil.rmtree(path)
        except FileExistsError as e:
            logging.warning(f'{path} > {e}')


def divide_list(list_string: list, size: int) -> list:
    """Функция возвращающая массив разделенный на равные части"""
    string_to_number = [string for string in list_string]
    divide = lambda lst, sz: [lst[i:i + sz] for i in range(0, len(lst), sz)]
    return divide(string_to_number, size)


async def get_user_role(user_id: Union[str, int]) -> str:
    if user_id in settings.bot.BOSS:
        return 'boss'
    else:
        return 'staff'


async def file_size_check(message: Message):
    try:
        get_type = await file_type(message)
        if get_type == 'photo':
            await message[f'{get_type}'][3].download()
        else:
            await message[f'{get_type}'].download()

        if os.path.exists(os.path.join(os.getcwd(), f'{get_type}s')):
            shutil.rmtree(os.path.join(os.getcwd(), f'{get_type}s'))

    except:
        logging.error(
            f'FileIsTooBig > id: {message.message_id} от: {message.from_user.username}, {message.from_user.id}')
        await message.answer(
            f'Файл слишком большой!!!\n'
            f'Разрешено: 5МБ для фото, 20МБ для остальных файлов.')
        return True


async def file_type(message: Message) -> str:
    message_types = {
        'video': message.video,
        'photo': message.photo,
        'audio': message.audio,
        'sticker': message.sticker,
        'animation': message.animation,
        'video_note': message.video_note
    }

    for key, value in message_types.items():
        if value:
            return key

    return 'document'


def includes_number(text):
    """Функция проверяющая строку на число"""
    return any(char.isdigit() for char in text)
    # return any(map(str.isdigit, text))


def subsets_combinations(nums: List[int | str]):
    results = [[]]
    for length in range(1, len(nums) + 1):
        results.extend(combinations(nums, length))
    stations = sorted(list(filter(lambda x: any(x), results)), key=lambda x: x[0])
    new_stations = [
        ', '.join([stations[i][0]] + list(stations[i][1:]))
        for i in range(len(stations))
        if len(stations[i]) > 1
    ]
    return tuple(new_stations)
