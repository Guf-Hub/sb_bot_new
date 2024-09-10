from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .repositories import (
    UserRepo,
    ProductRepo,
    WriteOffRepo,
    CheckCafeRepo,
    CheckRestaurantRepo,
    PointRepo,
    PositionRepo,
)
from core.config import settings

async_engine = create_async_engine(
    url=settings.db.URL_SQLITE if settings.use_sqlite else settings.db.url_postgres,
    echo=settings.db.ECHO,
    pool_pre_ping=True,
    poolclass=NullPool
)

async_session_factory = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session():
    async with async_session_factory() as session:
        yield session


class Database:
    """
    Database class is the highest abstraction level of database and
    can be used in the handlers or any others bot-side functions
    """

    """ User repository """
    user: UserRepo
    """ Product repository """
    product: ProductRepo
    """ WriteOff repository """
    write_off: WriteOffRepo
    """ CheckCafeRepo repository """
    check_cafe: CheckCafeRepo
    """ CheckCafeRepo repository """
    check_restaurant: CheckRestaurantRepo
    """ CheckDayRepo repository """
    point: PointRepo
    """ PositionRepo repository """
    position: PositionRepo

    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    @property
    def user(self) -> UserRepo:
        """
        The User repository sessions are required to manage user operations.
        """
        return UserRepo(self.session)

    @property
    def product(self) -> ProductRepo:
        """
        The Product repository sessions are required to manage Product operations.
        """
        return ProductRepo(self.session)

    @property
    def write_off(self) -> WriteOffRepo:
        """
        The WriteOff repository sessions are required to manage write_off operations.
        """
        return WriteOffRepo(self.session)

    @property
    def check_cafe(self) -> CheckCafeRepo:
        """
        The CheckCafeRepo repository sessions are required to manage check_day operations.
        """
        return CheckCafeRepo(self.session)

    @property
    def check_restaurant(self) -> CheckRestaurantRepo:
        """
        The CheckRestaurantRepo repository sessions are required to manage check_day operations.
        """
        return CheckRestaurantRepo(self.session)

    @property
    def point(self) -> PointRepo:
        """
        The Point repository sessions are required to manage point operations.
        """
        return PointRepo(self.session)

    @property
    def position(self) -> PositionRepo:
        """
        The Position repository sessions are required to manage default operations.
        """
        return PositionRepo(self.session)
