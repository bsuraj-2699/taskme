from routers.analytics import router as analytics_router
from routers.auth import router as auth_router
from routers.comments import router as comments_router
from routers.notifications import router as notifications_router
from routers.reports import router as reports_router
from routers.submissions import router as submissions_router
from routers.tasks import router as tasks_router
from routers.users import router as users_router

__all__ = [
    "analytics_router",
    "auth_router",
    "comments_router",
    "submissions_router",
    "tasks_router",
    "users_router",
    "notifications_router",
    "reports_router",
]

