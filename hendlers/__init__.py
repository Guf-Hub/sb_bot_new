from aiogram import Router
from .chats import router as chats_router
from .admin import router as admin_router
from .check.cafe import router as check_day_cafe_router
# from .check.restaurant import router as check_day_restaurant_router
from .charts import router as charts_router
from .expenses import router as expenses_router
from .write_off import router as write_off_router

router = Router(name=__name__)
router.include_routers(
    chats_router,
    charts_router,
    check_day_cafe_router,
    # check_day_restaurant_router,
    expenses_router,
    admin_router,
    write_off_router,
)

__all__ = ('router',)
