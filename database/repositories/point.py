from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from ..models import Point
from .abstract import Repository


class PointRepo(Repository[Point]):
    """Point repository for CRUD and other SQL queries"""

    def __init__(self, session: AsyncSession):
        """Initialize repository"""
        super().__init__(type_model=Point, session=session)

    async def add(self, point: Point) -> Point | None:
        result = await self.session.scalar(select(Point).where(Point.name == point.name))

        if not result:
            self.session.add(point)
            await self.session.commit()

        return point

    async def get_one(self, name: str):
        return await self.session.scalar(select(Point).where(Point.name == name))

    async def get_all(self):
        return await self.session.scalars(select(Point))

    async def get_alias(self, name: str):
        return await self.session.scalar(select(Point.alias).where(Point.name == name))

    async def update(self, **kwargs):
        name = kwargs.get('name')
        query = update(Point).where(Point.name == name).values(**kwargs)
        await self.session.execute(query)
        await self.session.commit()

    async def delete(self, name: str):
        query = delete(Point).where(Point.name == name)
        await self.session.execute(query)
        await self.session.commit()
