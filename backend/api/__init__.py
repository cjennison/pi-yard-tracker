"""
API module for Pi Yard Tracker

FastAPI REST API for querying photos and detections.

Usage:
    # Run the API server
    uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
    
    # Or run from Python
    python -m backend.api.main
"""

from .main import app

__all__ = ["app"]
