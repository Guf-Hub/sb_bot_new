import enum


class Role(enum.Enum):
    """ Roles """
    staff = "Сотрудник"
    supervisor = "Супервайзер"
    administrator = "Администратор"

    # master = "Мастер"

    @classmethod
    def values(cls):
        return tuple(role.value for role in cls)

    @classmethod
    def key(cls, value):
        return next((role.name for role in cls if role.value == value), None)
