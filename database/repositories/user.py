""" User repository file """
from typing import Optional, Type, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, literal, exists

from structures.role import Role

from ..models import User
from .abstract import Repository


class UserRepo(Repository[User]):
    """User repository for CRUD and other SQL queries"""

    def __init__(self, session: AsyncSession):
        """Initialize repository"""
        super().__init__(type_model=User, session=session)

    async def add(self, user: User) -> User | None:
        result = await self.session.scalar(select(User).where(User.user_id == user.user_id))

        if not result:
            # user.point = await session.scalar(select(Point.id).where(Point.name == user.point))
            # user.position = await session.scalar(select(Position.id).where(Position.name == user.position))
            self.session.add(user)
            await self.session.commit()
        return result

    async def get_one(self, user_id: int) -> User | None:
        return await self.session.scalar(select(User).where(User.user_id == user_id))

    async def is_exist(self, user_id: int) -> bool:
        return await self.session.scalar(
            exists().where(User.user_id == user_id)
        )

    async def get_one_by_pk(self, pk: int) -> User | None:
        return await self.session.scalar(select(User).where(User.id == pk))

    async def get_user_id_by_full_name(self, full_name: str) -> User.user_id | None:
        last_name, first_name = full_name.split(' ')
        return await self.session.scalar(
            select(User.user_id).where(User.first_name == first_name, User.last_name == last_name))

    async def get_all(self):
        return await self.session.scalars(select(User))
        # users = await self.session.scalars(select(User))
        # return users.all()

    async def get_active(self):
        users = await self.session.scalars(select(User).where(User.status))
        # for user in users:
        # user.point = await session.scalar(select(Point.name).where(Point.id == user.point))
        # user.position = await session.scalar(select(Position.name).where(Position.id == user.position))

        return users.all()

    async def is_active(self, user_id: int) -> bool:
        return (
                await self.session.scalar(
                    select(User.status).where(User.user_id == user_id)
                ) == True
        )

    async def get_supervisors(self):
        result = await self.session.scalars(select(User).where(User.role == Role.supervisor))
        return result.all()

    async def is_supervisors(self, user_id: int) -> bool:
        return (
                await self.session.scalar(
                    select(User.role).where(User.user_id == user_id)
                ) == Role.supervisor
        )

    async def get_hr(self) -> User | None:
        result = await self.session.scalar(select(User).where(User.position.contains('HR')))
        return result

    async def update(self, **kwargs) -> None:
        user_id = kwargs.get('user_id')
        query = update(User).where(User.user_id == user_id).values(**kwargs)
        await self.session.execute(query)
        await self.session.commit()

    async def delete(self, user_id: int) -> None:
        query = delete(User).where(User.user_id == user_id)
        await self.session.execute(query)
        await self.session.commit()
