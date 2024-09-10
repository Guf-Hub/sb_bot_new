import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import User
from .base import Base, int_pk


# class Category(Base):
#     __tablename__ = 'categories'
#
#     name: Mapped[str] = mapped_column(String(150), nullable=False)
#
#     def __repr__(self) -> str:
#         return (f"{self.__class__.__name__}("
#                 f"{self.id=}, "
#                 f"{self.name=}, "
#                 f"{self.created_at=}, "
#                 f"{self.updated_at=})")


class Product(Base):

    id: Mapped[int_pk]
    code: Mapped[int] = mapped_column(sa.Integer, nullable=False, unique=True)
    product: Mapped[str] = mapped_column(sa.String(255), nullable=True)  # name
    group_product: Mapped[str] = mapped_column(sa.String(255), nullable=True)  # category
    # group: Mapped[str] = mapped_column(sa.String(255), nullable=True)
    unit: Mapped[str] = mapped_column(sa.String(5), nullable=False)
    price: Mapped[float] = mapped_column(sa.Float(2), nullable=False, default=0)

    # price: Mapped[str] = mapped_column(sa.String(255), nullable=False)

    # category_id: Mapped[int] = mapped_column(sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    # category: Mapped['Category'] = relationship(backref='products')

    repr_cols_num = Base.get_num_keys()

    def to_dict(self):
        return {
            'code': self.code,
            'product': self.product,
            'group_product': self.group_product,
            'unit': self.unit,
            'price': self.price
        }


# class Cart(Base):
#
#     user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
#     product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
#     quantity: Mapped[int]
#
#     user: Mapped['User'] = relationship(backref='carts')
#     product: Mapped['Product'] = relationship(backref='carts')
#
#     def __repr__(self) -> str:
#         return (f"{self.__class__.__name__}("
#                 f"{self.id=}, "
#                 f"{self.user_id=}, "
#                 f"{self.product_id=}, "
#                 f"{self.quantity=}, "
#                 f"{self.created_at=}")
