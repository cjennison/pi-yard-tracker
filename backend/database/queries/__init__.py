"""
Database query functions organized by entity

This package provides high-level functions for CRUD operations.
"""

from .photos import (
    create_photo,
    get_photo,
    get_photos,
    update_photo_detections
)

from .detections import (
    create_detection,
    get_detections_for_photo,
    get_detections
)

from .sessions import (
    create_session,
    end_session,
    get_sessions
)

from .stats import (
    get_detection_stats
)

__all__ = [
    # Photo operations
    'create_photo',
    'get_photo',
    'get_photos',
    'update_photo_detections',
    
    # Detection operations
    'create_detection',
    'get_detections_for_photo',
    'get_detections',
    
    # Session operations
    'create_session',
    'end_session',
    'get_sessions',
    
    # Statistics
    'get_detection_stats',
]
