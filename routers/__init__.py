from .auth import router as auth_router
from .exam import router as exam_router
from .admin import router as admin_router

__all__ = [
    "auth_router",
    "exam_router",
    "admin_router"
]
