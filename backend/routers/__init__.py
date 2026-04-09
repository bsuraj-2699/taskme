from routers.auth import router as auth_router
from routers.notifications import router as notifications_router
from routers.reports import router as reports_router
from routers.tasks import router as tasks_router
from routers.users import router as users_router

__all__ = [
    "auth_router",
    "tasks_router",
    "users_router",
    "notifications_router",
    "reports_router",
]

