"""
Updated CameraCapture class that works with SharedCameraManager.

This modification allows camera_capture.py to work alongside the live streaming system
by using the shared camera resource instead of directly controlling the camera.
"""

import time
import os
from pathlib import Path
from datetime import datetime, timedelta
import threading
import logging
import argparse
from PIL import Image
import numpy as np

# Import shared camera manager
from backend.shared_camera import get_shared_camera

# Try to import YOLO, but allow running without it
try:
    from ultralytics import YOLO
    import cv2
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  YOLO not available - run without detection or install: pip install ultralytics opencv-python")

# Try to import database, but allow running without it
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
    print("⚠️  Database not available - detections will not be saved to database")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SharedCameraCapture:
    """
    Updated camera capture class that uses SharedCameraManager.
    
    This allows camera capture to work alongside live streaming by using
    the shared camera resource instead of directly controlling the camera.
    """
    
    def __init__(self, photo_dir: Path):
        self.photo_dir = photo_dir
        self.shared_camera = get_shared_camera()
        self.capture_buffer = None
        self.capture_ready = threading.Event()
        
        # Create photo directory if it doesn't exist
        self.photo_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Photo directory: {self.photo_dir.absolute()}")
        
        # Register callback with shared camera
        self.shared_camera.register_capture_callback(self._on_frame_received)
        
        # Start shared camera if not already started
        if not self.shared_camera.is_started:
            self.shared_camera.start()
        
        logger.info("📷 Using shared camera for photo capture")
    
    def _on_frame_received(self, frame: np.ndarray, frame_type: str):
        """Callback when shared camera provides a frame"""
        if frame_type == "capture":
            self.capture_buffer = frame.copy()
            self.capture_ready.set()
    
    def capture(self) -> Path:
        """Capture a single photo and return its path"""
        # Generate filename with timestamp
        timestamp = datetime.now()
        filename = f"capture_{timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.jpg"
        filepath = self.photo_dir / filename
        
        try:
            # Wait for next frame from shared camera (with timeout)
            self.capture_ready.clear()
            if self.capture_ready.wait(timeout=5.0):
                if self.capture_buffer is not None:
                    # Convert numpy array to PIL Image and save
                    pil_image = Image.fromarray(self.capture_buffer)
                    pil_image.save(filepath, 'JPEG', quality=95)
                    logger.info(f"📸 Captured: {filename}")
                    return filepath
                else:
                    logger.error("❌ No frame data available")
                    return None
            else:
                logger.error("❌ Timeout waiting for camera frame")
                return None
                
        except Exception as e:
            logger.error(f"❌ Capture failed: {e}")
            return None
    
    def cleanup(self):
        """Cleanup camera capture resources"""
        # Remove callback from shared camera
        self.shared_camera.remove_capture_callback(self._on_frame_received)
        logger.info("📷 Camera capture cleanup complete")


# Example of how to modify the main() function in camera_capture.py
def updated_main_example():
    """
    Example of how the main() function would be modified to use SharedCameraCapture
    """
    
    # Replace this line:
    # camera = CameraCapture(PHOTO_DIR, simulate=simulate)
    
    # With this:
    camera = SharedCameraCapture(PHOTO_DIR)
    
    # Everything else remains the same!
    # The detector, database integration, and main loop work identically
    
    # The key benefits:
    # 1. camera_capture.py continues to work exactly as before
    # 2. Live streaming can run simultaneously 
    # 3. Both systems share the same physical camera
    # 4. No conflicts or resource contention