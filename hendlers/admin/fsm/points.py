from aiogram.fsm.state import StatesGroup, State


class PointAdd(StatesGroup):
    """Класс для добавления новой точки"""
    NAME = State()
    # ADDRESS = State()
    # LATITUDE = State()
    # LONGITUDE = State()
    ALIAS = State()
    STATUS = State()


class PointUpdate(StatesGroup):
    """Класс для добавления новой точки"""
    NAME = State()
    ADDRESS = State()
    LATITUDE = State()
    LONGITUDE = State()
    ALIAS = State()
    STATUS = State()


class PointDelete(StatesGroup):
    """Класс для удаления точки"""
    NAME = State()
