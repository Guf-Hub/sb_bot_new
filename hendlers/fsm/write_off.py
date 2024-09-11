from aiogram.fsm.state import StatesGroup, State


class WriteOffAdd(StatesGroup):
    """Класс для сбора списаний"""
    POINT = State()
    CATEGORY = State()
    CODE = State()
    QUANTITY = State()
    REASON = State()
    COMMENT = State()
    FILE = State()
    NEXT = State()


class GrindSetting(StatesGroup):
    """Класс для сбора списаний по настройке помола кофемашины"""
    TYPE = State()
    POINT = State()
    CODE = State()
    QUANTITY = State()
    FILE = State()


class WriteOffSend(StatesGroup):
    """Класс для сбора списаний"""
    POINT = State()
