"""
Database query functions for CRUD operations

Provides high-level functions for working with photos and detections.

This module re-exports functions from the queries package for backward compatibility.
"""

# Re-export all query functions from organized modules
from .queries import *

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
