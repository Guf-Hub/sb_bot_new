from datetime import datetime
from typing import List

from sqlalchemy import select, update, delete, func, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .models import User, Point, Position, WriteOff, Product, CheckCafe


"""Работа с User"""


class DBHelper:
    @staticmethod
    async def user_add(
        session: AsyncSession,
        user: User,
    ):
        result = await session.scalar(select(User).where(User.user_id == user.user_id))

        if not result:
            # user.point = await session.scalar(select(Point.id).where(Point.name == user.point))
            # user.position = await session.scalar(select(Position.id).where(Position.name == user.position))
            session.add(user)
            await session.commit()

    @staticmethod
    async def user_get(session: AsyncSession, user_id: int | str):
        return await session.scalar(select(User).where(User.user_id == user_id))
        # return await session.scalar(select(User).where(cast(User.user_id, String) == user_id))

    @staticmethod
    async def user_by_pk_get(session: AsyncSession, pk: int):
        return await session.scalar(select(User).where(User.id == pk))

    @staticmethod
    async def user_get_user_id_by_full_name(session: AsyncSession, full_name: str):
        last_name, first_name = full_name.split(" ")
        return await session.scalar(
            select(User.user_id).where(
                User.first_name == first_name, User.last_name == last_name
            )
        )

    @staticmethod
    async def users_get(session: AsyncSession):
        return await session.scalars(select(User))

    @staticmethod
    async def users_active_get(session: AsyncSession):
        users = await session.scalars(select(User).where(User.status))
        # for user in users:
        # user.point = await session.scalar(select(Point.name).where(Point.id == user.point))
        # user.position = await session.scalar(select(Position.name).where(Position.id == user.position))

        return users

    @staticmethod
    async def user_is_active(session: AsyncSession, user_id: int | str):
        return (
            await session.scalar(select(User.status).where(User.user_id == user_id))
            == True
        )

    @staticmethod
    async def users_supervisors_get(session: AsyncSession):
        return await session.scalars(select(User).where(User.is_supervisor))

    @staticmethod
    async def users_is_supervisors(session: AsyncSession, user_id: int | str):
        return (
            await session.scalar(
                select(User.is_supervisor).where(User.user_id == user_id)
            )
            == True
        )

    @staticmethod
    async def users_hr_get(session: AsyncSession):
        return await session.scalar(select(User).where(User.position.contains("HR")))

    @staticmethod
    async def user_update(session: AsyncSession, **kwargs):
        user_id = kwargs.get("user_id")
        query = update(User).where(User.user_id == user_id).values(**kwargs)
        await session.execute(query)
        await session.commit()

    @staticmethod
    async def user_delete(session: AsyncSession, user_id: int | str):
        query = delete(User).where(User.user_id == user_id)
        await session.execute(query)
        await session.commit()

    @staticmethod
    async def point_position_get(session: AsyncSession, point: str, position: str):
        point = await session.scalar(select(Point).where(Point.name == point))
        position = await session.scalar(
            select(Position).where(Position.name == position)
        )
        return point, position

    """Работа с Point"""

    @staticmethod
    async def point_add(session: AsyncSession, point: Point):
        result = await session.scalar(select(Point).where(Point.name == point.name))

        if not result:
            session.add(point)
            await session.commit()

    @staticmethod
    async def point_get(session: AsyncSession, name: str):
        return await session.scalar(select(Point).where(Point.name == name))

    @staticmethod
    async def points_get(session: AsyncSession):
        return await session.scalars(select(Point))

    @staticmethod
    async def point_alias_get(session: AsyncSession, name: str):
        return await session.scalar(select(Point.alias).where(Point.name == name))

    @staticmethod
    async def point_update(session: AsyncSession, **kwargs):
        name = kwargs.get("name")
        query = update(Point).where(Point.name == name).values(**kwargs)
        await session.execute(query)
        await session.commit()

    @staticmethod
    async def point_delete(session: AsyncSession, name: str):
        query = delete(Point).where(Point.name == name)
        await session.execute(query)
        await session.commit()

    """Работа с Position"""

    @staticmethod
    async def position_add(session: AsyncSession, position: Position):
        result = await session.scalar(
            select(Position).where(Position.name == position.name)
        )

        if not result:
            session.add(position)
            await session.commit()

    @staticmethod
    async def position_get(session: AsyncSession, name: str):
        return await session.scalar(select(Position).where(Position.name == name))

    """Работа с WriteOff"""

    @staticmethod
    async def write_off_add(session: AsyncSession, write_off: WriteOff):
        session.add(write_off)
        await session.commit()

    @staticmethod
    async def limit_setting_coffee_query(
        session: AsyncSession, point: str, comment: str
    ):
        return await session.scalar(
            select(func.sum(WriteOff.quantity))
            .where(func.date(WriteOff.created_at) == func.date(datetime.now()))
            .
            # where(func.date(WriteOff.created_at) == func.date(func.datetime('now', '+3 hour'))).
            where(WriteOff.comment == comment)
            .where(WriteOff.point == point)
        )

    """Работа с CheckCafe"""

    @staticmethod
    async def check_day_add(session: AsyncSession, check_day: CheckCafe):
        session.add(check_day)
        await session.commit()
        return check_day.id

    @staticmethod
    async def check_day_get(session: AsyncSession, report_id: int):
        return await session.scalar(
            select(CheckCafe)
            .options(
                joinedload(CheckCafe.user),
            )
            .where(CheckCafe.id == report_id)
        )

    @staticmethod
    async def check_day_reports_get_by_date(session: AsyncSession, date: str):
        return await session.scalars(
            select(CheckCafe)
            .options(
                joinedload(CheckCafe.user),
            )
            .where(CheckCafe.add_date == date)
        )

    @staticmethod
    async def check_day_update(session: AsyncSession, report_id: int, **kwargs):
        query = update(CheckCafe).where(CheckCafe.id == report_id).values(**kwargs)
        await session.execute(query)
        await session.commit()

    @staticmethod
    async def check_day_is_unique_report_by_date(
        session: AsyncSession, point: str, report_type: str, date: str
    ):
        """Check if a report for a specific date already exists in the database (check_day)"""
        return await session.scalar(
            select(CheckCafe)
            .options(joinedload(CheckCafe.user))
            .where(
                CheckCafe.point == point,
                CheckCafe.type == report_type,
                CheckCafe.add_date == date,
            )
        )

    @staticmethod
    async def check_day_reports_get(
        session: AsyncSession, date_start: str, date_end: str
    ):
        return await session.execute(
            select(
                CheckCafe.supervisor.label("sv"),
                CheckCafe.type,
                func.count(CheckCafe.in_time).label("count_in_time"),
                func.sum(CheckCafe.in_time).label("sum_in_time"),
                (
                    func.sum(
                        func.ifnull(
                            func.strftime("%s", CheckCafe.created_at)
                            - func.strftime("%s", CheckCafe.created_at),
                            0,
                        )
                    )
                    / func.count(CheckCafe.created_at)
                ).label("avg_check_datetime"),
            )
            .select_from(CheckCafe)
            .where(CheckCafe.add_date.between(date_start, date_end))
            .group_by(CheckCafe.supervisor, CheckCafe.type)
            .order_by(CheckCafe.supervisor.asc(), CheckCafe.type.desc())
            .scalars()
        ).all()

    """
    /*SELECT supervisor AS sv, type, COUNT(in_time), SUM(in_time),
                    SUM(IFNULL(STRFTIME('%s', updated_at) - STRFTIME('%s', created_at),0))/COUNT(updated_at)
                    FROM checkdays WHERE add_date BETWEEN '2024-07-01' AND '2024-07-29'  GROUP BY sv, type 
                    ORDER BY sv ASC, type DESC;*/


    /*SELECT supervisor AS sv, type, COUNT(in_time), SUM(in_time),
                    SUM(IFNULL(STRFTIME('%s', check_datetime) - STRFTIME('%s', add_datetime),0))/COUNT(check_datetime)
                    FROM check_day WHERE add_date BETWEEN '2024-07-01' AND '2024-07-29'  GROUP BY sv, type 
                    ORDER BY sv ASC, type DESC;*/

    """

    ######################## Работа с товарами #######################################
    @staticmethod
    async def product_add(
        session: AsyncSession,
        product: Product,
    ):
        result = await session.scalar(
            select(Product).where(Product.code == product.code)
        )

        if not result:
            session.add(product)
            await session.commit()
        else:
            query = (
                update(Product)
                .where(Product.code == product.code)
                .values(**product.to_dict())
            )
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def product_add_many(session: AsyncSession, products: List[Product]):
        codes = [p.code for p in products]
        existing_products = await session.execute(
            select(Product).where(Product.code.in_(codes))
        )
        existing_codes = {product.code for product in existing_products.scalars().all()}

        new_products = [
            product for product in products if product.code not in existing_codes
        ]

        if new_products:
            session.add_all(new_products)
            await session.commit()

    @staticmethod
    async def product_category(session: AsyncSession):
        unique_values = await session.scalars(
            select(Product.group_product)
            .distinct()
            .order_by(Product.group_product.asc())
        )

        return unique_values

    @staticmethod
    async def products_get_by_category(session: AsyncSession, category: str):
        return await session.scalars(
            select(Product)
            .where(Product.group_product == category)
            .order_by(Product.product.asc())
        )

    @staticmethod
    async def product_get(session: AsyncSession, code: int | str):
        return await session.scalar(select(Product).where(Product.code == int(code)))

    @staticmethod
    async def products_get(session: AsyncSession):
        return await session.scalars(select(Product))

    @staticmethod
    async def product_delete(session: AsyncSession, code: int | str):
        query = delete(Product).where(Product.code == int(code))
        await session.execute(query)
        await session.commit()


db = DBHelper()
