"""
Statistics and session API routes

Endpoints for overall statistics and detection sessions.
"""

from fastapi import APIRouter, Query
from typing import List

from backend.database import get_detection_stats, get_sessions
from ..schemas import StatsResponse, SessionResponse

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """
    Get overall detection statistics
    
    Returns:
    - Total photos captured
    - Photos with detections
    - Total detections made
    - Breakdown by object class
    """
    stats = get_detection_stats()
    return StatsResponse(**stats)


@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of sessions to return")
):
    """
    Get recent detection sessions
    
    Shows history of camera capture runs with their statistics.
    
    - **limit**: Maximum sessions to return (1-100, default 10)
    """
    sessions = get_sessions(limit=limit)
    return [SessionResponse(**session.to_dict()) for session in sessions]
