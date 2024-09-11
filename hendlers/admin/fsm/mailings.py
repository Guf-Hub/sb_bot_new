from aiogram.fsm.state import StatesGroup, State


class Mailing(StatesGroup):
    """Класс массовой рассылки по сотрудникам"""
    TEXT = State()
