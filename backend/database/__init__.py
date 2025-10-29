"""
Database module for Pi Yard Tracker

Provides database connection, models, and query functions for storing
photos and detection results.

Usage:
    from backend.database import get_db, create_photo, create_detection
    
    # Create photo record
    photo_id = create_photo("yard_001.jpg", "/path/to/photo.jpg")
    
    # Create detection record
    detection_id = create_detection(
        photo_id=photo_id,
        class_name="deer",
        confidence=0.85,
        bbox_x=0.5,
        bbox_y=0.5,
        bbox_width=0.3,
        bbox_height=0.4
    )
"""

from .db import Database, get_db
from .models import Photo, Detection, DetectionSession
from .queries import (
    # Photo operations
    create_photo,
    get_photo,
    get_photos,
    update_photo_detections,
    # Detection operations
    create_detection,
    get_detections_for_photo,
    get_detections,
    # Session operations
    create_session,
    end_session,
    get_sessions,
    # Statistics
    get_detection_stats,
)

__all__ = [
    # Database
    "Database",
    "get_db",
    # Models
    "Photo",
    "Detection",
    "DetectionSession",
    # Photo operations
    "create_photo",
    "get_photo",
    "get_photos",
    "update_photo_detections",
    # Detection operations
    "create_detection",
    "get_detections_for_photo",
    "get_detections",
    # Session operations
    "create_session",
    "end_session",
    "get_sessions",
    # Statistics
    "get_detection_stats",
]
