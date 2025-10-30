"""
Statistics and aggregation queries
"""

from ..db import get_db


def get_detection_stats() -> dict:
    """
    Get overall detection statistics
    
    Returns:
        Dictionary with stats including:
        - total_photos: Total number of photos
        - photos_with_detections: Photos that have detections
        - total_detections: Total number of detections
        - unique_classes: Number of unique object classes
        - avg_confidence: Average detection confidence
        - top_classes: Most detected classes
    """
    return get_db().get_stats()
