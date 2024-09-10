from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from ..models import Product
from .abstract import Repository


class ProductRepo(Repository[Product]):
    """Product repository for CRUD and other SQL queries"""

    def __init__(self, session: AsyncSession):
        """Initialize repository"""
        super().__init__(type_model=Product, session=session)

    async def add(self, product: Product):
        result = await self.session.scalar(select(Product).where(Product.code == int(product.code)))

        if not result:
            self.session.add(product)
            await self.session.commit()
        else:
            query = update(Product).where(Product.code == int(product.code)).values(**product.to_dict())
            await self.session.execute(query)
            await self.session.commit()

    async def add_many(self, products: List[Product]):
        codes = [p.code for p in products]
        existing_products = await self.session.execute(select(Product).where(Product.code.in_(codes)))
        existing_codes = {product.code for product in existing_products.scalars().all()}

        new_products = [product for product in products if product.code not in existing_codes]

        if new_products:
            self.session.add_all(new_products)
            await self.session.commit()

    async def add_all(self, products: List[Product]):
        self.session.add_all(products)
        await self.session.commit()

    async def get_one(self, code: int | str):
        return await self.session.scalar(select(Product).where(Product.code == int(code)))

    async def get_all(self):
        return await self.session.scalars(select(Product))

    async def get_all_by_category(self, category: str):
        return await self.session.scalars(
            select(Product).where(Product.group_product == category).order_by(Product.product.asc()))

    async def category(self):
        unique_values = await self.session.scalars(
            select(Product.group_product).distinct().order_by(Product.group_product.asc()))

        return unique_values

    async def delete(self, code: int | str) -> None:
        query = delete(Product).where(Product.code == int(code))
        await self.session.execute(query)
        await self.session.commit()
