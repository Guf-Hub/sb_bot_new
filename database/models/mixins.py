from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import declared_attr, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .user import User


class UserRelationMixin:
    _user_id_nullable: bool = False
    _user_id_unique: bool = False
    _user_back_populates: str | None = None

    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return mapped_column(
            ForeignKey("users.id", ondelete='CASCADE'),
            unique=cls._user_id_unique,
            nullable=cls._user_id_nullable
        )

    @declared_attr
    def user(cls) -> Mapped["User"]:
        return relationship(
            "User",
            back_populates=cls._user_back_populates
        )


# class SupervisorRelationMixin:
#     _supervisor_id_nullable: bool = True
#     _supervisor_id_unique: bool = False
#     _supervisor_back_populates: str | None = None
#
#     @declared_attr
#     def supervisor_id(cls) -> Mapped[int]:
#         return mapped_column(
#             ForeignKey("users.id", ondelete='CASCADE'),
#             unique=cls._supervisor_id_unique,
#             nullable=cls._supervisor_id_nullable
#         )
#
#     @declared_attr
#     def supervisor(cls) -> Mapped["User"]:
#         return relationship(
#             "User",
#             back_populates=cls._supervisor_back_populates
#         )
