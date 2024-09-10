from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

from ..models import  WriteOff
from .abstract import Repository


class WriteOffRepo(Repository[WriteOff]):
    """WriteOff repository for CRUD and other SQL queries"""

    def __init__(self, session: AsyncSession):
        """Initialize repository"""
        super().__init__(type_model=WriteOff, session=session)

    async def limit_setting_coffee_query(self, point: str, comment: str):
        return await self.session.scalar(
            select(func.sum(WriteOff.quantity)).
            where(func.date(WriteOff.created_at) == func.date(datetime.now())).
            where(WriteOff.comment == comment).
            where(WriteOff.point == point)
        )

    async def update(self, **kwargs) -> WriteOff:
        write_off_id = kwargs.get('id')
        query = update(WriteOff).where(WriteOff.id == write_off_id).values(**kwargs)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one()

    async def delete(self, write_off_id: int) -> None:
        query = delete(WriteOff).where(WriteOff.id == write_off_id)
        await self.session.execute(query)
        await self.session.commit()
