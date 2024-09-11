from aiogram.fsm.state import StatesGroup, State


class Morning(StatesGroup):
    """Класс для сбора Утреннего отчета"""
    type_key = State()
    type = State()
    point = State()
    user_id = State()
    question_one = State()
    file1 = State()
    file2 = State()
    file3 = State()


class Evening(StatesGroup):
    """Класс для сбора Вечернего отчета"""
    date = State()
    type = State()
    point = State()
    user_id = State()
    file1 = State()
    file2 = State()
    file3 = State()
    file4 = State()
    file5 = State()
    file6 = State()
    file7 = State()


class CheckRestaurantReport(StatesGroup):
    """Класс для сборки данных подтверждения проверки отчета"""
    report_id = State()
    comment = State()
