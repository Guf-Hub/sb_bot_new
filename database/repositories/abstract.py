""" Repository file """
import abc
from typing import Generic, List, Type, TypeVar
from collections.abc import Sequence

from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Base

AbstractModel = TypeVar("AbstractModel")


class Repository(Generic[AbstractModel]):
    """Repository abstract class"""

    type_model: Type[Base]
    session: AsyncSession

    def __init__(self, type_model: Type[Base], session: AsyncSession):
        """
        Initialize abstract repository class
        :param type_model: Which model will be used for operations
        :param session: Session in which repository will work
        """
        self.type_model = type_model
        self.session = session

    async def get(self, ident: int | str) -> AbstractModel:
        """
        Get an ONE model from the database with PK
        :param ident: Key which need to find entry in database
        :return:
        """
        return await self.session.get(entity=self.type_model, ident=ident)

    async def get_by_where(self, where_clause) -> AbstractModel | None:
        """
        Get an ONE model from the database with where_clause
        :param where_clause: Clause by which entry will be found
        :return: Model if only one model was found, else None
        """
        statement = select(self.type_model).where(where_clause)
        return (await self.session.execute(statement)).one_or_none()

    async def get_many(
            self, where_clause, limit: int = 1000, order_by=None
    ) -> Sequence[Base]:
        """
        Get many models from the database with where_clause
        :param where_clause: Where clause for finding models
        :param limit: (Optional) Limit count of results
        :param order_by: (Optional) Order by clause

        Example:
        >> Repository.get_many(Model.id == 1, limit=1000, order_by=Model.id)

        :return: List of founded models
        """
        statement = select(self.type_model).where(where_clause).limit(limit)
        if order_by:
            statement = statement.order_by(order_by)

        return (await self.session.scalars(statement)).all()

    async def add(self, model: AbstractModel) -> None:
        """
        Add a new model to the repository

        :param model: The model to add
        :return: Nothing
        """
        self.session.add(model)
        await self.session.commit()

    async def insert(self, **kwargs) -> AbstractModel:
        """
        Insert a new model into the database

        :param kwargs: Keyword arguments representing the fields of the new model
        :return: Nothing
        """
        statement = insert(self.type_model).values(**kwargs).returning(self.type_model)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.scalar_one()

    async def update(self, where_clause, **kwargs) -> AbstractModel:
        """
        Update a model in the database

        :param where_clause: Clause by which entry will be found
        :param kwargs: Keyword arguments representing the fields to update
        :return: Nothing
        """
        statement = update(self.type_model).where(where_clause).values(**kwargs).returning(self.type_model)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.scalar_one()

    async def delete(self, where_clause) -> None:
        """
        Delete model from the database

        :param where_clause: (Optional) Which statement
        :return: Nothing
        """
        statement = delete(self.type_model).where(where_clause)
        await self.session.execute(statement)
        await self.session.commit()

    # @abc.abstractmethod
    # async def new(self, *args, **kwargs) -> None:
    #     """
    #     This method is need to be implemented in child classes,
    #     it is responsible for adding a new model to the database
    #     :return: Nothing
    #     """
    #     ...
