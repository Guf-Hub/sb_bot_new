import asyncio
import logging

from sqlalchemy import text, delete
from database import async_engine, async_session_factory, Database
from database.models import Base, Position, Point, User
from structures.keybords import company_positions, company_points
from structures.role import Role


async def create_db():
    try:
        async with async_engine.begin() as conn:

            async_engine.echo = False
            await conn.run_sync(Base.metadata.create_all)

        async with async_session_factory() as session:
            db = Database(session)

            for position in company_positions:
                await db.position.add(Position(name=position))
            for point in company_points:
                await db.point.add(Point(**point))

            await db.user.add(
                User(
                    user_id=6968474689,
                    first_name="сервисный",
                    last_name="Бот",
                    position="Тест",
                    point="Офис",
                    role=Role.administrator
                ))

            async_engine.echo = True
            logging.info("Database created successfully")
    except Exception as e:
        logging.error("Create database error: %s", e, exc_info=True)
        logging.error("Database connection string: %s", async_engine.url.password)


async def drop_db():
    try:
        async with async_engine.begin() as conn:
            async_engine.echo = False
            await conn.run_sync(Base.metadata.drop_all)
            async_engine.echo = True
    except Exception as e:
        logging.error("Drop database error: %s", e, exc_info=True)


async def truncate_table(table):
    try:
        async with async_session_factory() as session:
            async_engine.echo = True
            await session.execute(delete(table))
            await session.commit()
            async_engine.echo = True
    except Exception as e:
        logging.error("Drop table error: %s", e, exc_info=True)


async def drop_tables(tables):
    try:
        async with async_engine.begin() as conn:
            async_engine.echo = False
            tables = [table.__table__ for table in tables]
            await conn.run_sync(Base.metadata.drop_all, tables=tables, checkfirst=True)
    except Exception as e:
        logging.error("Drop tables error: %s", e, exc_info=True)
