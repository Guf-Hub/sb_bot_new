from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String, BigInteger, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from structures.role import Role
from .base import Base, int_pk

if TYPE_CHECKING:
    from .write_off import WriteOff
    from .check_day import CheckDay


class User(Base):
    # id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(30), nullable=True)
    last_name: Mapped[str] = mapped_column(String(30), nullable=True)

    point = mapped_column(ForeignKey("points.name"), nullable=False)
    position = mapped_column(ForeignKey("positions.name"), nullable=False)

    write_offs: Mapped[List["WriteOff"]] = relationship(back_populates="user")
    check_days: Mapped[List["CheckDay"]] = relationship(back_populates="user")

    # is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    # is_supervisor: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    points: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.staff)
    status: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    @hybrid_property
    def full_name(self) -> str:
        return f"{self.last_name} {self.first_name}"
        # return f"{self.first_name} {self.last_name}"

    repr_cols_num = 12
    # repr_cols = ("created_at", )

    # def __repr__(self) -> str:
    #     return (f"{self.__class__.__name__}("
    #             f"{self.id=}, "
    #             f"{self.user_id=}, "
    #             f"{self.first_name=}, "
    #             f"{self.last_name=}, "
    #             f"{self.full_name=}, "
    #             f"{self.point=}, "
    #             f"{self.position=}, "
    #             f"{self.is_admin=}, "
    #             f"{self.is_supervisor=}, "
    #             f"{self.points=}, "
    #             f"{self.status=}, "
    #             f"{self.created_at=}, "
    #             f"{self.updated_at=})")
