"""
Live object detection for streaming video

Handles real-time YOLO detection on video frames with normalized bounding boxes.
"""

import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Try to import YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("⚠️  YOLO not available for live detection")


class LiveDetector:
    """
    Real-time object detector for live camera streams
    
    Lightweight wrapper around YOLO for low-latency detection
    """
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.25):
        """
        Initialize live detector
        
        Args:
            model_path: Path to YOLO model file
            confidence_threshold: Minimum detection confidence
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.detector = None
        
        if YOLO_AVAILABLE:
            try:
                logger.info(f"🤖 Loading YOLO model for live detection: {model_path}")
                self.detector = YOLO(model_path)
                logger.info("✅ Live detector ready")
            except Exception as e:
                logger.error(f"❌ Failed to load live detector: {e}")
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Run detection on video frame
        
        Args:
            frame: RGB numpy array (H, W, 3)
        
        Returns:
            List of detection dictionaries with normalized bounding boxes
        """
        if not self.detector:
            return []
        
        try:
            # Run detection
            results = self.detector.predict(
                source=frame,
                conf=self.confidence_threshold,
                verbose=False,
                device='cpu'  # Force CPU for real-time processing
            )
            
            # Parse results
            detections = []
            result = results[0]
            
            height, width = frame.shape[:2]
            
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = self.detector.names[class_id]
                confidence = float(box.conf[0])
                
                # Get bounding box coordinates (pixels)
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                # Calculate normalized coordinates (0-1 range)
                x_center = (x1 + x2) / 2 / width
                y_center = (y1 + y2) / 2 / height
                bbox_width = (x2 - x1) / width
                bbox_height = (y2 - y1) / height
                
                detections.append({
                    "id": f"live_{int(time.time() * 1000)}_{len(detections)}",
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": {
                        "x_min": x1 / width,
                        "y_min": y1 / height,
                        "x_max": x2 / width,
                        "y_max": y2 / height,
                        "x_center": x_center,
                        "y_center": y_center,
                        "width": bbox_width,
                        "height": bbox_height
                    },
                    "timestamp": datetime.now().isoformat()
                })
            
            return detections
            
        except Exception as e:
            logger.debug(f"⚠️  Detection error: {e}")
            return []
    
    def update_confidence_threshold(self, threshold: float):
        """
        Update detection confidence threshold
        
        Args:
            threshold: New threshold (0.0 - 1.0)
        """
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        logger.info(f"🎯 Updated live detection confidence: {self.confidence_threshold}")
