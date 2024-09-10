from aiogram.fsm.state import StatesGroup, State


class EmployeeAdd(StatesGroup):
    """Класс для добавления нового сотрудника в БД(users)"""
    USER_ID = State()
    FULL_NAME = State()
    POSITION = State()
    POINT = State()
    ROLE = State()
    POINTS = State()
    STATUS = State()


class EmployeeUpdate(StatesGroup):
    """Класс для обновления данных по сотруднику в БД(users)"""
    USER_ID = State()
    FULL_NAME = State()
    POSITION = State()
    POINT = State()
    ROLE = State()
    POINTS = State()


class EmployeeDelete(StatesGroup):
    """Класс для удаления сотрудника из БД(users)"""
    FULL_NAME = State()


class EmployeeActivate(StatesGroup):
    """Класс для активации сотрудника в БД(users)"""
    FULL_NAME = State()


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


class Mailing(StatesGroup):
    """Класс массовой рассылки по сотрудникам"""
    TEXT = State()
