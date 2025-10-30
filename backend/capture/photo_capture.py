"""
Photo capture service

Handles continuous photo capture from the shared camera with detection and database integration.
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

# Import database functions
try:
    from backend.database import (
        create_photo,
        create_detection,
        update_photo_detections,
        create_session,
        end_session
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger.warning("⚠️  Database not available - detections will not be saved")


class PhotoCaptureService:
    """
    Service that captures photos from shared camera and runs detection
    
    Uses callback-based architecture to receive frames from SharedCameraManager
    """
    
    def __init__(
        self,
        shared_camera,
        photo_dir: Path,
        detector=None,
        interval: float = 10.0,
        model_name: Optional[str] = None,
        confidence: float = 0.25
    ):
        """
        Initialize photo capture service
        
        Args:
            shared_camera: SharedCameraManager instance
            photo_dir: Directory to save photos
            detector: YOLODetector instance (optional)
            interval: Capture interval in seconds
            model_name: Model name for database tracking
            confidence: Detection confidence threshold
        """
        self.shared_camera = shared_camera
        self.photo_dir = Path(photo_dir)
        self.detector = detector
        self.interval = interval
        self.model_name = model_name
        self.confidence = confidence
        
        self.capture_count = 0
        self.detection_count = 0
        self.session_id = None
        self.last_capture_time = 0
        self.running = False
        
        logger.info(f"📷 Photo capture initialized")
        logger.info(f"   Directory: {self.photo_dir}")
        logger.info(f"   Interval: {self.interval}s")
        if self.detector:
            logger.info(f"   Detector: {self.model_name} @ {self.confidence}")
    
    def start(self):
        """Start the capture service"""
        self.running = True
        
        # Create database session if available
        if DATABASE_AVAILABLE and self.detector:
            try:
                self.session_id = create_session(
                    model_name=self.model_name,
                    confidence_threshold=self.confidence
                )
                logger.info(f"🎬 Created database session {self.session_id}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to create database session: {e}")
        
        # Register callback with shared camera
        self.shared_camera.register_capture_callback(self._handle_frame)
        logger.info("✅ Photo capture service started")
    
    def stop(self):
        """Stop the capture service"""
        self.running = False
        
        # Unregister callback
        self.shared_camera.remove_capture_callback(self._handle_frame)
        
        # End database session
        if DATABASE_AVAILABLE and self.session_id:
            try:
                end_session(self.session_id, self.capture_count, self.detection_count)
                logger.info(f"🎬 Ended database session {self.session_id}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to end database session: {e}")
        
        logger.info("✅ Photo capture service stopped")
    
    def _handle_frame(self, frame, frame_type):
        """Callback to handle captured frames"""
        # Only process capture frames (not stream frames)
        if frame_type != "capture":
            return
        
        # Respect the interval setting
        current_time = time.time()
        if current_time - self.last_capture_time < self.interval:
            return
        
        self.last_capture_time = current_time
        
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"photo_{timestamp}.jpg"
            photo_path = self.photo_dir / filename
            
            # Save frame as JPEG
            img = Image.fromarray(frame)
            img.save(photo_path, 'JPEG', quality=95)
            
            self.capture_count += 1
            photo_id = None
            
            # Save photo to database
            if DATABASE_AVAILABLE:
                try:
                    width, height = img.size
                    photo_id = create_photo(
                        filename=filename,
                        filepath=str(photo_path.absolute()),
                        width=width,
                        height=height,
                        captured_at=datetime.now()
                    )
                    logger.debug(f"💾 Saved photo to database (ID: {photo_id})")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to save photo to database: {e}")
            
            # Run detection if detector available
            if self.detector:
                detections = self.detector.detect(photo_path, save_visualization=True)
                if detections:
                    self.detection_count += 1
                    logger.info(f"🦌 Found {len(detections)} objects in {filename}")
                    
                    # Save detections to database
                    if DATABASE_AVAILABLE and photo_id:
                        self._save_detections_to_db(photo_id, detections)
            
            # Log every 10 captures
            if self.capture_count % 10 == 0:
                logger.info(f"📊 {self.capture_count} photos, {self.detection_count} with detections")
        
        except Exception as e:
            logger.error(f"❌ Error processing frame: {e}")
    
    def _save_detections_to_db(self, photo_id: int, detections: list):
        """Save detections to database"""
        try:
            for det in detections:
                bbox_norm = det['bbox_norm']
                create_detection(
                    photo_id=photo_id,
                    class_name=det['class'],
                    confidence=det['confidence'],
                    bbox_x=bbox_norm['x'],
                    bbox_y=bbox_norm['y'],
                    bbox_width=bbox_norm['width'],
                    bbox_height=bbox_norm['height'],
                    model_name=self.model_name
                )
            
            # Update photo detection count
            update_photo_detections(photo_id, len(detections))
            logger.debug(f"💾 Saved {len(detections)} detections to database")
        except Exception as e:
            logger.warning(f"⚠️  Failed to save detections to database: {e}")
