"""
API route modules

Exports all API routers for registration with FastAPI app.
"""

from .photos import router as photos_router
from .detections import router as detections_router
from .stats import router as stats_router

__all__ = [
    "photos_router",
    "detections_router",
    "stats_router",
]
