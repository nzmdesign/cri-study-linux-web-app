from routers.admin import router as admin_router
from routers.auth import router as auth_router
from routers.exam import router as exam_router
from routers.health import router as health_router
from routers.index import router as index_router

__all__ = [
    "admin_router",
    "auth_router",
    "exam_router",
    "health_router",
    "index_router"
]
