"""API routers package."""
from .upload import router as upload_router
from .detection import router as detection_router
from .results import router as results_router

__all__ = ["upload_router", "detection_router", "results_router"]
