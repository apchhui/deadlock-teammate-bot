from .handlers_menu import router as menu_router
from .handlers_profile import router as profile_router
from .handlers_browse import router as browse_router

__all__ = ["menu_router", "profile_router", "browse_router"]
