from sqlalchemy import String, Boolean, DateTime, func, Float
from sqlalchemy.orm import Mapped, mapped_column

from .mixins import UserRelationMixin
from .base import Base, int_pk


class Point(Base):
    # _user_id_unique = True
    # _user_back_populates = "point"

    id: Mapped[int_pk]
    name: Mapped[str] = mapped_column(String(50), unique=True)
    address: Mapped[str] = mapped_column(String(200), nullable=True, default=None, server_default=None)
    latitude: Mapped[float] = mapped_column(Float, nullable=True, default=None, server_default=None)
    longitude: Mapped[float] = mapped_column(Float, nullable=True, default=None, server_default=None)
    alias: Mapped[str] = mapped_column(String(3))
    status: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    repr_cols_num = Base.get_num_keys()
