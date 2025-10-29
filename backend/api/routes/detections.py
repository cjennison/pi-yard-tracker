"""
Detection API routes

Endpoints for querying object detections.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime

from backend.database import get_detections
from ..schemas import DetectionResponse

router = APIRouter(prefix="/detections", tags=["detections"])


@router.get("/", response_model=List[DetectionResponse])
def list_detections(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of detections to return"),
    offset: int = Query(0, ge=0, description="Number of detections to skip (pagination)"),
    class_name: Optional[str] = Query(None, description="Filter by object class"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    start_date: Optional[str] = Query(None, description="Filter detections after this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter detections before this date (ISO format)")
):
    """
    Get list of detections with optional filtering
    
    - **limit**: Maximum detections to return (1-500, default 100)
    - **offset**: Pagination offset (default 0)
    - **class_name**: Filter by object class (e.g., "coffee_mug", "deer")
    - **min_confidence**: Minimum confidence (0.0-1.0)
    - **start_date**: ISO datetime string (e.g., "2025-10-29T00:00:00")
    - **end_date**: ISO datetime string
    """
    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    # Query database
    detections = get_detections(
        limit=limit,
        offset=offset,
        class_name=class_name,
        min_confidence=min_confidence,
        start_date=start_dt,
        end_date=end_dt
    )
    
    # Convert to response format
    return [DetectionResponse(**det.to_dict()) for det in detections]


@router.get("/classes")
def list_detection_classes():
    """
    Get list of all detected object classes with counts
    
    Returns aggregated statistics for each class that has been detected.
    """
    from backend.database import get_detection_stats
    
    stats = get_detection_stats()
    return {
        "classes": stats['detection_classes'],
        "total_detections": stats['total_detections']
    }
