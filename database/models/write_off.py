from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .mixins import UserRelationMixin
from .base import Base, int_pk


class WriteOff(UserRelationMixin, Base):

    _user_back_populates = "write_offs"

    id: Mapped[int_pk]
    point: Mapped[str] = mapped_column(String(50))
    # employee: Mapped[str] = mapped_column(String(50))
    code: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(50))
    comment: Mapped[str] = mapped_column(String(255), nullable=True, default="Нет", server_default="Нет")
    file: Mapped[str] = mapped_column(String(1000), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=True)

    repr_cols_num = Base.get_num_keys()
