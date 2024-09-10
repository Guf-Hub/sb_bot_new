import json
from typing import Annotated

import pytz
from sqlalchemy import DateTime, Integer, func, MetaData, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr

from datetime import datetime, date, timezone

from core.config import settings


class DateTimeEncoder(json.JSONEncoder):
    """Класс для записи дат в JSON"""

    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, bytes):
            return list(o)
        return json.JSONEncoder.default(self, o)


metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

int_pk = Annotated[int, mapped_column(Integer, autoincrement=True, primary_key=True)]


moscow_tz = pytz.timezone("Europe/Moscow")

if settings.use_sqlite:
    created_at = Annotated[
        datetime,
        mapped_column(
            DateTime(timezone=True), default=func.now(), server_default=func.now()
        ),
    ]

    updated_at = Annotated[
        datetime,
        mapped_column(
            DateTime(timezone=True),
            default=func.now(),
            onupdate=func.now(),
            server_default=func.now(),
        ),
    ]

else:
    created_at = Annotated[
        datetime, mapped_column(server_default=text("TIMEZONE('Europe/Moscow', now())"))
    ]
    updated_at = Annotated[
        datetime,
        mapped_column(
            server_default=text("TIMEZONE('Europe/Moscow', now())"),
            onupdate=datetime.now(),
        ),
    ]

# created_at = Annotated[datetime, mapped_column(server_default=text("TIMEZONE('Europe/Moscow', now())"))]
# updated_at = Annotated[datetime, mapped_column(
#     server_default=text("TIMEZONE('Europe/Moscow', now())"),
#     onupdate=datetime.now(),
# )]

str_50 = Annotated[str, 50]
str_256 = Annotated[str, 256]
str_1000 = Annotated[str, 1000]


class Base(DeclarativeBase):
    __abstract__ = True
    _set_plural: bool = True

    type_annotation_map = {
        str_50: String(50),
        str_256: String(256),
        str_1000: String(1000),
    }

    @declared_attr
    def __tablename__(cls) -> str:
        # return f"{cls.__name__.lower()}s"
        return (
            cls.camel_to_snake(cls.__name__) + "s"
            if cls._set_plural
            else cls.camel_to_snake(cls.__name__)
        )

    __allow_unmapped__ = False

    # id: Mapped[int_pk]
    # created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    # updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now(),
    #                                              server_default=func.now())

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        """Relationships не используются в repr(), т.к. могут вести к неожиданным подгрузкам"""
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"{self.__class__.__name__}({', '.join(cols)})"

    @classmethod
    def camel_to_snake(cls, cls_name: str) -> str:
        return "".join(
            ["_" + i.lower() if i.isupper() else i for i in cls_name]
        ).lstrip("_")

    @classmethod
    def get_num_keys(cls):
        return len([attr for attr in dir(cls) if not attr.startswith("__")])

    def to_json(self):
        return json.dumps(
            self.to_dict(), indent=2, ensure_ascii=False, cls=DateTimeEncoder
        )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
