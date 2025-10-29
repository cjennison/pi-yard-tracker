"""
Database query functions for CRUD operations

Provides high-level functions for working with photos and detections.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
import logging

from .db import get_db
from .models import Photo, Detection, DetectionSession

logger = logging.getLogger(__name__)


# ============================================================
# Photo Operations
# ============================================================

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


# ============================================================
# Detection Operations
# ============================================================

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


# ============================================================
# Session Operations
# ============================================================

def create_session(
    model_name: Optional[str] = None,
    confidence_threshold: Optional[float] = None
) -> int:
    """
    Create a new detection session
    
    Args:
        model_name: Name of model being used
        confidence_threshold: Confidence threshold setting
    
    Returns:
        Session ID
    """
    db = get_db()
    
    query = """
        INSERT INTO detection_sessions (model_name, confidence_threshold)
        VALUES (?, ?)
    """
    
    session_id = db.execute_insert(query, (model_name, confidence_threshold))
    logger.info(f"🎬 Started detection session {session_id}")
    return session_id


def end_session(session_id: int, photo_count: int, detection_count: int):
    """
    End a detection session with final counts
    
    Args:
        session_id: Session ID
        photo_count: Total photos captured
        detection_count: Total detections made
    """
    db = get_db()
    
    query = """
        UPDATE detection_sessions
        SET ended_at = ?, photo_count = ?, detection_count = ?
        WHERE id = ?
    """
    
    db.execute_update(query, (datetime.now().isoformat(), photo_count, detection_count, session_id))
    logger.info(f"🎬 Ended detection session {session_id}: {photo_count} photos, {detection_count} detections")


def get_sessions(limit: int = 10) -> List[DetectionSession]:
    """
    Get recent detection sessions
    
    Args:
        limit: Maximum number of sessions to return
    
    Returns:
        List of DetectionSession objects
    """
    db = get_db()
    query = "SELECT * FROM detection_sessions ORDER BY started_at DESC LIMIT ?"
    rows = db.execute_query(query, (limit,))
    
    return [DetectionSession.from_row(row) for row in rows]


# ============================================================
# Statistics
# ============================================================

def get_detection_stats() -> dict:
    """
    Get overall detection statistics
    
    Returns:
        Dictionary with stats
    """
    return get_db().get_stats()
