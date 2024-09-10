from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import Position
from .abstract import Repository


class PositionRepo(Repository[Position]):
    """Position repository for CRUD and other SQL queries"""

    def __init__(self, session: AsyncSession):
        """Initialize repository"""
        super().__init__(type_model=Position, session=session)

    async def add(self, position: Position):
        result = await self.session.scalar(select(Position).where(Position.name == position.name))

        if not result:
            self.session.add(position)
            await self.session.commit()

    async def get_one(self, name: str):
        return await self.session.scalar(select(Position).where(Position.name == name))
