from aiogram import Router
from .chats import router as chats_router

from .admin.employee import router as admin_employee_router
from .admin.points import router as admin_points_router
from .admin.reports import router as admin_reports_router
from .admin.mailings import router as admin_mailings_router
from .admin.expenses import router as admin_expenses_router

from .check.cafe import router as check_day_cafe_router
from .check.reports import router as check_day_reports_router
# from .check.restaurant import router as check_day_restaurant_router
from .charts import router as charts_router

from .write_off.write_off import router as write_off_router

router = Router(name=__name__)
router.include_routers(
    chats_router,
    charts_router,

    check_day_cafe_router,
    check_day_reports_router,
    # check_day_restaurant_router,

    admin_employee_router,
    admin_points_router,
    admin_mailings_router,
    admin_reports_router,
    admin_expenses_router,

    write_off_router,
)

__all__ = ('router',)
