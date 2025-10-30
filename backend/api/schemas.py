"""
Pydantic schemas for API request/response validation

Defines the structure of data sent to and from the API.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class BoundingBox(BaseModel):
    """Bounding box coordinates (normalized 0-1)"""
    # YOLO format (center coordinates)
    x: float = Field(..., ge=0.0, le=1.0, description="Center x coordinate")
    y: float = Field(..., ge=0.0, le=1.0, description="Center y coordinate")
    width: float = Field(..., ge=0.0, le=1.0, description="Box width")
    height: float = Field(..., ge=0.0, le=1.0, description="Box height")
    
    # Derived coordinates for frontend (optional, calculated by backend)
    x_center: Optional[float] = None
    y_center: Optional[float] = None
    x_min: Optional[float] = None
    y_min: Optional[float] = None
    x_max: Optional[float] = None
    y_max: Optional[float] = None


class DetectionResponse(BaseModel):
    """Detection record response"""
    id: int
    photo_id: int
    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    model_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "photo_id": 42,
                "class_name": "coffee_mug",
                "confidence": 0.85,
                "bbox": {
                    "x": 0.5,
                    "y": 0.5,
                    "width": 0.3,
                    "height": 0.4
                },
                "model_name": "custom_model/weights/best.pt",
                "created_at": "2025-10-29T10:00:00"
            }
        }


class PhotoResponse(BaseModel):
    """Photo record response"""
    id: int
    filename: str
    filepath: str
    width: Optional[int] = None
    height: Optional[int] = None
    captured_at: datetime
    has_detections: bool
    detection_count: int
    created_at: datetime
    marked_for_retraining: bool = False
    marked_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 42,
                "filename": "yard_20251029_100000.jpg",
                "filepath": "/data/photos/yard_20251029_100000.jpg",
                "width": 1920,
                "height": 1080,
                "captured_at": "2025-10-29T10:00:00",
                "has_detections": True,
                "detection_count": 2,
                "created_at": "2025-10-29T10:00:00",
                "marked_for_retraining": False,
                "marked_at": None
            }
        }


class PhotoWithDetections(PhotoResponse):
    """Photo with its detections included"""
    detections: List[DetectionResponse] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 42,
                "filename": "yard_20251029_100000.jpg",
                "filepath": "/data/photos/yard_20251029_100000.jpg",
                "captured_at": "2025-10-29T10:00:00",
                "has_detections": True,
                "detection_count": 1,
                "detections": [
                    {
                        "id": 1,
                        "photo_id": 42,
                        "class_name": "coffee_mug",
                        "confidence": 0.85,
                        "bbox": {"x": 0.5, "y": 0.5, "width": 0.3, "height": 0.4}
                    }
                ]
            }
        }


class SessionResponse(BaseModel):
    """Detection session response"""
    id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    model_name: Optional[str] = None
    confidence_threshold: Optional[float] = None
    photo_count: int
    detection_count: int


class StatsResponse(BaseModel):
    """Overall statistics response"""
    total_photos: int
    photos_with_detections: int
    total_detections: int
    detection_classes: List[dict]
    avg_detections_per_photo: float
    unique_classes: int
    most_detected_class: Optional[str] = None
    latest_photo_time: Optional[str] = None
    oldest_photo_time: Optional[str] = None
    active_session_id: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_photos": 150,
                "photos_with_detections": 45,
                "total_detections": 67,
                "detection_classes": [
                    {"class_name": "coffee_mug", "count": 35},
                    {"class_name": "person", "count": 20},
                    {"class_name": "cat", "count": 12}
                ],
                "avg_detections_per_photo": 0.45,
                "unique_classes": 3,
                "most_detected_class": "coffee_mug",
                "latest_photo_time": "2025-10-29T10:00:00",
                "oldest_photo_time": "2025-10-28T08:00:00",
                "active_session_id": 5
            }
        }


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper"""
    total: int
    limit: int
    offset: int
    items: List[dict]  # Can be photos, detections, etc.


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: str
    version: str
