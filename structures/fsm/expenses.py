from aiogram.fsm.state import StatesGroup, State


class Home(StatesGroup):
    """Класс для сбора расходов на строительство дома"""
    category = State()
    type = State()
    amount = State()
    comment = State()


class Payments(StatesGroup):
    """Класс сбор Расходов"""
    date = State()
    point = State()
    category = State()
    amount = State()
    comment = State()
    file = State()


class Projects(StatesGroup):
    """Класс сбор Расходов на проекты"""
    point = State()
    category = State()
    type = State()
    amount = State()
    comment = State()
    file = State()
