"""
Photo-related database queries
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional
import logging

from ..db import get_db
from ..models import Photo

logger = logging.getLogger(__name__)


def create_photo(
    filename: str,
    filepath: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    captured_at: Optional[datetime] = None
) -> int:
    """
    Insert a new photo record
    
    Args:
        filename: Photo filename
        filepath: Full path to photo
        width: Image width in pixels
        height: Image height in pixels
        captured_at: Timestamp when captured
    
    Returns:
        Photo ID
    """
    db = get_db()
    
    if captured_at is None:
        captured_at = datetime.now()
    
    query = """
        INSERT INTO photos (filename, filepath, width, height, captured_at)
        VALUES (?, ?, ?, ?, ?)
    """
    
    photo_id = db.execute_insert(
        query,
        (filename, filepath, width, height, captured_at.isoformat())
    )
    
    logger.debug(f"📝 Created photo record: {filename} (ID: {photo_id})")
    return photo_id


def get_photo(photo_id: int) -> Optional[Photo]:
    """
    Get a photo by ID
    
    Args:
        photo_id: Photo ID
    
    Returns:
        Photo object or None
    """
    db = get_db()
    query = "SELECT * FROM photos WHERE id = ?"
    rows = db.execute_query(query, (photo_id,))
    
    if rows:
        return Photo.from_row(rows[0])
    return None


def get_photos(
    limit: int = 100,
    offset: int = 0,
    has_detections: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Photo]:
    """
    Get photos with optional filtering
    
    Args:
        limit: Maximum number of photos to return
        offset: Number of photos to skip (pagination)
        has_detections: Filter by detection presence
        start_date: Filter photos after this date
        end_date: Filter photos before this date
    
    Returns:
        List of Photo objects
    """
    db = get_db()
    
    conditions = []
    params = []
    
    if has_detections is not None:
        conditions.append("has_detections = ?")
        params.append(1 if has_detections else 0)
    
    if start_date:
        conditions.append("captured_at >= ?")
        params.append(start_date.isoformat())
    
    if end_date:
        conditions.append("captured_at <= ?")
        params.append(end_date.isoformat())
    
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    query = f"""
        SELECT * FROM photos
        {where_clause}
        ORDER BY captured_at DESC
        LIMIT ? OFFSET ?
    """
    
    params.extend([limit, offset])
    rows = db.execute_query(query, tuple(params))
    
    return [Photo.from_row(row) for row in rows]


def update_photo_detections(photo_id: int, detection_count: int):
    """
    Update photo's detection count
    
    Args:
        photo_id: Photo ID
        detection_count: Number of detections
    """
    db = get_db()
    query = """
        UPDATE photos 
        SET has_detections = ?, detection_count = ?
        WHERE id = ?
    """
    db.execute_update(query, (1 if detection_count > 0 else 0, detection_count, photo_id))
