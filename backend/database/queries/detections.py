"""
Detection-related database queries
"""

from datetime import datetime
from typing import List, Optional
import logging

from ..db import get_db
from ..models import Detection

logger = logging.getLogger(__name__)


def create_detection(
    photo_id: int,
    class_name: str,
    confidence: float,
    bbox_x: float,
    bbox_y: float,
    bbox_width: float,
    bbox_height: float,
    model_name: Optional[str] = None
) -> int:
    """
    Insert a new detection record
    
    Args:
        photo_id: Associated photo ID
        class_name: Detected object class
        confidence: Detection confidence (0-1)
        bbox_x: Bounding box center x (normalized)
        bbox_y: Bounding box center y (normalized)
        bbox_width: Bounding box width (normalized)
        bbox_height: Bounding box height (normalized)
        model_name: Name of model used
    
    Returns:
        Detection ID
    """
    db = get_db()
    
    query = """
        INSERT INTO detections 
        (photo_id, class_name, confidence, bbox_x, bbox_y, bbox_width, bbox_height, model_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    detection_id = db.execute_insert(
        query,
        (photo_id, class_name, confidence, bbox_x, bbox_y, bbox_width, bbox_height, model_name)
    )
    
    logger.debug(f"📝 Created detection: {class_name} ({confidence:.2%}) for photo {photo_id}")
    return detection_id


def get_detections_for_photo(photo_id: int) -> List[Detection]:
    """
    Get all detections for a specific photo
    
    Args:
        photo_id: Photo ID
    
    Returns:
        List of Detection objects
    """
    db = get_db()
    query = "SELECT * FROM detections WHERE photo_id = ? ORDER BY confidence DESC"
    rows = db.execute_query(query, (photo_id,))
    
    return [Detection.from_row(row) for row in rows]


def get_detections(
    limit: int = 100,
    offset: int = 0,
    class_name: Optional[str] = None,
    min_confidence: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Detection]:
    """
    Get detections with optional filtering
    
    Args:
        limit: Maximum number of detections to return
        offset: Number of detections to skip (pagination)
        class_name: Filter by class name
        min_confidence: Minimum confidence threshold
        start_date: Filter detections after this date
        end_date: Filter detections before this date
    
    Returns:
        List of Detection objects
    """
    db = get_db()
    
    conditions = []
    params = []
    
    if class_name:
        conditions.append("class_name = ?")
        params.append(class_name)
    
    if min_confidence is not None:
        conditions.append("confidence >= ?")
        params.append(min_confidence)
    
    if start_date:
        conditions.append("created_at >= ?")
        params.append(start_date.isoformat())
    
    if end_date:
        conditions.append("created_at <= ?")
        params.append(end_date.isoformat())
    
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    query = f"""
        SELECT * FROM detections
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    
    params.extend([limit, offset])
    rows = db.execute_query(query, tuple(params))
    
    return [Detection.from_row(row) for row in rows]
