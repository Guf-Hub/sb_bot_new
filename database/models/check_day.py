from sqlalchemy import Date, String, Boolean, Time
from sqlalchemy.orm import Mapped, mapped_column

from .mixins import UserRelationMixin
from .base import Base, int_pk


class CheckCafe(UserRelationMixin, Base):
    _set_plural = False
    _user_back_populates = "check_cafe"

    id: Mapped[int_pk]
    add_date: Mapped[str] = mapped_column(Date)
    type: Mapped[str] = mapped_column(String(30))
    point: Mapped[str] = mapped_column(String(30))
    question_one: Mapped[str] = mapped_column(String(10), nullable=True)
    files_id: Mapped[str] = mapped_column(String(1000))
    verified: Mapped[bool] = mapped_column(Boolean, default=0, server_default="0")
    comment: Mapped[str] = mapped_column(String(255), default='Нет', server_default="Нет")
    in_time: Mapped[bool] = mapped_column(Boolean, default=0, server_default="0")
    supervisor: Mapped[str] = mapped_column(String(30), nullable=True)
    duration = mapped_column(Time, nullable=True)

    repr_cols_num = Base.get_num_keys()
    repr_cols = ("user_id",)


class CheckRestaurant(UserRelationMixin, Base):
    _set_plural = False
    _user_back_populates = "check_restaurant"

    id: Mapped[int_pk]
    add_date: Mapped[str] = mapped_column(Date)
    type: Mapped[str] = mapped_column(String(30))
    point: Mapped[str] = mapped_column(String(30))
    question_one: Mapped[str] = mapped_column(String(10), nullable=True)
    files_id: Mapped[str] = mapped_column(String(1000))
    verified: Mapped[bool] = mapped_column(Boolean, default=0, server_default="0")
    comment: Mapped[str] = mapped_column(String(255), default='Нет', server_default="Нет")
    in_time: Mapped[bool] = mapped_column(Boolean, default=0, server_default="0")
    supervisor: Mapped[str] = mapped_column(String(30), nullable=True)
    duration = mapped_column(Time, nullable=True)

    repr_cols_num = Base.get_num_keys()
    repr_cols = ("user_id",)
