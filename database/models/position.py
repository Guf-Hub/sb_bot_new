from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from .mixins import UserRelationMixin
from .base import Base, int_pk, str_50


class Position(Base):
    # _user_id_unique = True
    # _user_back_populates = "position"

    id: Mapped[int_pk]
    name: Mapped[str_50] = mapped_column(nullable=False, unique=True)

    repr_cols_num = Base.get_num_keys()
