from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, cast, Date
from sqlalchemy.orm import joinedload

from ..models import CheckDay
from .abstract import Repository


class CheckDayRepo(Repository[CheckDay]):
    """
    User repository for CRUD and other SQL queries
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize user repository as for all users or only for one user
        """
        super().__init__(type_model=CheckDay, session=session)

    async def add(self, check_day: CheckDay) -> int:
        self.session.add(check_day)
        await self.session.commit()
        return check_day.id

    async def get_by_id(self, report_id: int):
        return await self.session.scalar(select(CheckDay).options(
            joinedload(CheckDay.user),
        ).where(CheckDay.id == report_id))

    async def get_reports_by_date(self, date: str):
        return await self.session.scalars(select(CheckDay).options(
            joinedload(CheckDay.user),
        ).where(CheckDay.add_date.cast(Date) == datetime.strptime(date, '%Y-%m-%d').date()))

    async def update(self, report_id: int, **kwargs):
        query = update(CheckDay).where(CheckDay.id == report_id).values(**kwargs)
        await self.session.execute(query)
        await self.session.commit()

    async def is_unique_report_by_date(self, point: str, report_type: str, date: str):
        """Check if a report for a specific date already exists in the database (check_day)"""
        return await self.session.scalar(
            select(CheckDay).options(joinedload(CheckDay.user)).where(CheckDay.point == point,
                                                                      CheckDay.type == report_type,
                                                                      CheckDay.add_date.cast(Date) == datetime.strptime(
                                                                          date, '%Y-%m-%d').date()))

    async def get_reports_by_period(self, start_date: str, end_date: str):
        """
        SELECT supervisor AS sv, type, COUNT(in_time), SUM(in_time),
                SUM(IFNULL(STRFTIME('%s', updated_at) - STRFTIME('%s', created_at),0))/COUNT(updated_at)
                FROM checkdays WHERE add_date BETWEEN ? AND ?  GROUP BY sv, type
                ORDER BY sv ASC, type DESC;
        """
        query = (
            select(
                CheckDay.supervisor.label('sv'),
                CheckDay.type,
                func.count(CheckDay.in_time).label('count_in_time'),
                func.sum(CheckDay.in_time).label('sum_in_time'),
                # func.sum(
                #     func.ifnull(
                #         func.strftime('%s', CheckDay.updated_at) - func.strftime('%s', CheckDay.created_at), 0))
                # / func.count(CheckDay.updated_at).label('avg_check_datetime'
            )
            .where(CheckDay.add_date.between(start_date, end_date))
            .group_by(CheckDay.supervisor, CheckDay.type)
            .order_by(CheckDay.supervisor.asc(), CheckDay.type.desc())
        )

        result = await self.session.execute(query)
        return result.scalars().all()

        # return await self.session.scalars(query)
