"""
Detection session database queries
"""

from datetime import datetime
from typing import List, Optional
import logging

from ..db import get_db
from ..models import DetectionSession

logger = logging.getLogger(__name__)


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
