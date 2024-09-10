from sqlalchemy import String, Boolean, DateTime, func, Float
from sqlalchemy.orm import Mapped, mapped_column

from .mixins import UserRelationMixin
from .base import Base


class Point(Base):
    # _user_id_unique = True
    # _user_back_populates = "point"

    name: Mapped[str] = mapped_column(String(50), unique=True)
    address: Mapped[str] = mapped_column(String(200), nullable=True, default=None, server_default=None)
    latitude: Mapped[float] = mapped_column(Float, nullable=True, default=None, server_default=None)
    longitude: Mapped[float] = mapped_column(Float, nullable=True, default=None, server_default=None)
    alias: Mapped[str] = mapped_column(String(3))
    status: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    # def __repr__(self) -> str:
    #     return (f"{self.__class__.__name__}("
    #             f"{self.id=}, "
    #             f"{self.name=}, "
    #             f"{self.address=}, "
    #             f"{self.latitude=}, "
    #             f"{self.longitude=}, "
    #             f"{self.alias=}), "
    #             f"{self.status=}, "
    #             f"{self.created_at=}, "
    #             f"{self.updated_at=})")