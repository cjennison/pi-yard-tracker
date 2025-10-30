"""
Photo API routes

Endpoints for querying photos and their metadata.
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from backend.database import get_photos, get_photo, get_detections_for_photo
from ..schemas import PhotoResponse, PhotoWithDetections

router = APIRouter(prefix="/photos", tags=["photos"])


@router.get("/", response_model=List[PhotoWithDetections])
def list_photos(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of photos to return"),
    offset: int = Query(0, ge=0, description="Number of photos to skip (pagination)"),
    has_detections: Optional[bool] = Query(None, description="Filter by detection presence"),
    start_date: Optional[str] = Query(None, description="Filter photos after this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter photos before this date (ISO format)")
):
    """
    Get list of photos with optional filtering
    
    - **limit**: Maximum photos to return (1-500, default 100)
    - **offset**: Pagination offset (default 0)
    - **has_detections**: Filter by detection presence (true/false)
    - **start_date**: ISO datetime string (e.g., "2025-10-29T00:00:00")
    - **end_date**: ISO datetime string
    """
    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    # Query database
    photos = get_photos(
        limit=limit,
        offset=offset,
        has_detections=has_detections,
        start_date=start_dt,
        end_date=end_dt
    )
    
    # Convert to response format with detections
    result = []
    for photo in photos:
        photo_dict = photo.to_dict()
        # Get detections for this photo
        detections = get_detections_for_photo(photo.id)
        photo_dict['detections'] = [det.to_dict() for det in detections]
        result.append(PhotoWithDetections(**photo_dict))
    
    return result


@router.get("/{photo_id}", response_model=PhotoWithDetections)
def get_photo_detail(photo_id: int):
    """
    Get a specific photo by ID with its detections
    
    - **photo_id**: Photo ID
    """
    # Get photo
    photo = get_photo(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail=f"Photo {photo_id} not found")
    
    # Get detections for this photo
    detections = get_detections_for_photo(photo_id)
    
    # Build response
    photo_dict = photo.to_dict()
    photo_dict['detections'] = [det.to_dict() for det in detections]
    
    return PhotoWithDetections(**photo_dict)


@router.get("/{photo_id}/detections")
def get_photo_detections(photo_id: int):
    """
    Get all detections for a specific photo
    
    - **photo_id**: Photo ID
    """
    # Verify photo exists
    photo = get_photo(photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail=f"Photo {photo_id} not found")
    
    # Get detections
    detections = get_detections_for_photo(photo_id)
    
    return [det.to_dict() for det in detections]


@router.get("/image/{filename}")
def get_photo_image(filename: str):
    """
    Serve photo image file
    
    - **filename**: Photo filename (e.g., capture_20251029_123456_789.jpg)
    """
    # Construct file path (assuming photos are in data/photos)
    photo_path = Path("data/photos") / filename
    
    # Security check - ensure filename doesn't contain path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Check if file exists
    if not photo_path.exists():
        raise HTTPException(status_code=404, detail=f"Photo file not found: {filename}")
    
    # Return file response
    return FileResponse(
        path=str(photo_path),
        media_type="image/jpeg",
        filename=filename
    )
