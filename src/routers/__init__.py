from .auth_router import router as auth_router
from .exam_router import router as exam_router
from .admin_router import router as admin_router
from .health_router import router as health_router
from .index_router import router as index_router

__all__ = [
    "auth_router",
    "exam_router",
    "admin_router",
    "health_router",
    "index_router"
]
