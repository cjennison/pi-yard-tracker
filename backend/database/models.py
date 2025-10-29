"""
Database models for photos and detections

Provides Python classes for database records with type hints.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Photo:
    """Photo record from database"""
    id: Optional[int]
    filename: str
    filepath: str
    width: Optional[int]
    height: Optional[int]
    captured_at: datetime
    has_detections: bool
    detection_count: int
    created_at: datetime
    
    @classmethod
    def from_row(cls, row) -> 'Photo':
        """Create Photo from database row"""
        return cls(
            id=row['id'],
            filename=row['filename'],
            filepath=row['filepath'],
            width=row['width'],
            height=row['height'],
            captured_at=datetime.fromisoformat(row['captured_at']),
            has_detections=bool(row['has_detections']),
            detection_count=row['detection_count'],
            created_at=datetime.fromisoformat(row['created_at'])
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "filename": self.filename,
            "filepath": self.filepath,
            "width": self.width,
            "height": self.height,
            "captured_at": self.captured_at.isoformat(),
            "has_detections": self.has_detections,
            "detection_count": self.detection_count,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Detection:
    """Detection record from database"""
    id: Optional[int]
    photo_id: int
    class_name: str
    confidence: float
    bbox_x: float
    bbox_y: float
    bbox_width: float
    bbox_height: float
    model_name: Optional[str]
    created_at: datetime
    
    @classmethod
    def from_row(cls, row) -> 'Detection':
        """Create Detection from database row"""
        return cls(
            id=row['id'],
            photo_id=row['photo_id'],
            class_name=row['class_name'],
            confidence=row['confidence'],
            bbox_x=row['bbox_x'],
            bbox_y=row['bbox_y'],
            bbox_width=row['bbox_width'],
            bbox_height=row['bbox_height'],
            model_name=row.get('model_name'),
            created_at=datetime.fromisoformat(row['created_at'])
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "photo_id": self.photo_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": {
                "x": self.bbox_x,
                "y": self.bbox_y,
                "width": self.bbox_width,
                "height": self.bbox_height
            },
            "model_name": self.model_name,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class DetectionSession:
    """Detection session record from database"""
    id: Optional[int]
    started_at: datetime
    ended_at: Optional[datetime]
    model_name: Optional[str]
    confidence_threshold: Optional[float]
    photo_count: int
    detection_count: int
    
    @classmethod
    def from_row(cls, row) -> 'DetectionSession':
        """Create DetectionSession from database row"""
        return cls(
            id=row['id'],
            started_at=datetime.fromisoformat(row['started_at']),
            ended_at=datetime.fromisoformat(row['ended_at']) if row['ended_at'] else None,
            model_name=row.get('model_name'),
            confidence_threshold=row.get('confidence_threshold'),
            photo_count=row['photo_count'],
            detection_count=row['detection_count']
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "model_name": self.model_name,
            "confidence_threshold": self.confidence_threshold,
            "photo_count": self.photo_count,
            "detection_count": self.detection_count
        }
