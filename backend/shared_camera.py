"""
Shared Camera Resource Manager

Manages camera access between the main capture system and live streaming.
Ensures both systems can work simultaneously without conflicts.
"""

import threading
import time
import logging
from typing import Optional, Callable
from datetime import datetime

# Try to import picamera2
try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

logger = logging.getLogger(__name__)

class SharedCameraManager:
    """
    Singleton camera manager that coordinates access between:
    1. Main capture system (saves photos to disk)
    2. Live streaming system (WebSocket feed)
    
    Uses a single camera instance with dual output streams.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.camera = None
        self.is_started = False
        self.capture_callbacks = []
        self.stream_callbacks = []
        self._capture_thread = None
        self._should_stop = False
        
        logger.info("📷 Initializing shared camera manager")
        self._init_camera()
    
    def _init_camera(self):
        """Initialize the camera with dual output configuration"""
        if not CAMERA_AVAILABLE:
            logger.warning("📷 Camera not available - operating in simulation mode")
            return
        
        try:
            self.camera = Picamera2()
            
            # Configure camera for both still capture and video streaming
            # Main output: High resolution for photo capture
            # Lores output: Lower resolution for live streaming
            config = self.camera.create_still_configuration(
                main={"size": (1920, 1080), "format": "RGB888"},  # For photo capture
                lores={"size": (640, 480), "format": "RGB888"},   # For live streaming
                display="lores"
            )
            
            self.camera.configure(config)
            logger.info("📷 Camera configured: 1920x1080 (capture) + 640x480 (stream)")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize camera: {e}")
            self.camera = None
    
    def start(self):
        """Start the camera and capture thread"""
        if self.is_started:
            return
        
        logger.info("🚀 Starting shared camera system")
        
        if self.camera:
            try:
                self.camera.start()
                time.sleep(2)  # Give camera time to adjust
                logger.info("📷 Camera started successfully")
            except Exception as e:
                logger.error(f"❌ Failed to start camera: {e}")
                return
        
        # Start capture thread
        self.is_started = True
        self._should_stop = False
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
        
        logger.info("✅ Shared camera system ready")
    
    def stop(self):
        """Stop the camera and capture thread"""
        if not self.is_started:
            return
        
        logger.info("🛑 Stopping shared camera system")
        self._should_stop = True
        self.is_started = False
        
        # Wait for capture thread
        if self._capture_thread:
            self._capture_thread.join(timeout=3)
        
        # Stop camera
        if self.camera:
            try:
                self.camera.stop()
                logger.info("📷 Camera stopped")
            except Exception as e:
                logger.debug(f"⚠️  Error stopping camera: {e}")
    
    def register_capture_callback(self, callback: Callable):
        """Register callback for photo capture events"""
        self.capture_callbacks.append(callback)
        logger.debug(f"📝 Registered capture callback (total: {len(self.capture_callbacks)})")
    
    def register_stream_callback(self, callback: Callable):
        """Register callback for live stream frames"""
        self.stream_callbacks.append(callback)
        logger.debug(f"📝 Registered stream callback (total: {len(self.stream_callbacks)})")
    
    def remove_capture_callback(self, callback: Callable):
        """Remove capture callback"""
        if callback in self.capture_callbacks:
            self.capture_callbacks.remove(callback)
    
    def remove_stream_callback(self, callback: Callable):
        """Remove stream callback"""
        if callback in self.stream_callbacks:
            self.stream_callbacks.remove(callback)
    
    def _capture_loop(self):
        """Main capture loop - handles both photo capture and live streaming"""
        last_capture_time = 0
        capture_interval = 1.0  # 1 second for photo capture
        stream_interval = 0.1   # 10 FPS for live streaming
        last_stream_time = 0
        
        while not self._should_stop:
            try:
                current_time = time.time()
                
                # Handle photo capture (every 1 second)
                if current_time - last_capture_time >= capture_interval:
                    if self.capture_callbacks:
                        self._handle_photo_capture()
                    last_capture_time = current_time
                
                # Handle live streaming (every 0.1 seconds = 10 FPS)
                if current_time - last_stream_time >= stream_interval:
                    if self.stream_callbacks:
                        self._handle_live_stream()
                    last_stream_time = current_time
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"❌ Error in capture loop: {e}")
                time.sleep(0.5)
    
    def _handle_photo_capture(self):
        """Handle photo capture for the main capture system"""
        try:
            if self.camera and CAMERA_AVAILABLE:
                # Capture high-resolution image from main output
                array = self.camera.capture_array("main")
            else:
                # Simulation mode
                import numpy as np
                array = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            
            # Notify all capture callbacks
            for callback in self.capture_callbacks[:]:
                try:
                    callback(array, "capture")
                except Exception as e:
                    logger.debug(f"⚠️  Capture callback error: {e}")
                    
        except Exception as e:
            logger.debug(f"⚠️  Photo capture error: {e}")
    
    def _handle_live_stream(self):
        """Handle frame capture for live streaming"""
        try:
            if self.camera and CAMERA_AVAILABLE:
                # Capture lower-resolution image from lores output
                array = self.camera.capture_array("lores")
            else:
                # Simulation mode
                import numpy as np
                array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                
                # Add simulation indicators
                import cv2
                cv2.putText(array, "LIVE SIMULATION", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(array, f"{datetime.now().strftime('%H:%M:%S')}", 
                           (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Notify all stream callbacks
            for callback in self.stream_callbacks[:]:
                try:
                    callback(array, "stream")
                except Exception as e:
                    logger.debug(f"⚠️  Stream callback error: {e}")
                    
        except Exception as e:
            logger.debug(f"⚠️  Live stream error: {e}")
    
    def get_camera_info(self):
        """Get camera information"""
        if self.camera and CAMERA_AVAILABLE:
            return {
                "available": True,
                "started": self.is_started,
                "capture_callbacks": len(self.capture_callbacks),
                "stream_callbacks": len(self.stream_callbacks)
            }
        else:
            return {
                "available": False,
                "started": self.is_started,
                "simulation": True,
                "capture_callbacks": len(self.capture_callbacks),
                "stream_callbacks": len(self.stream_callbacks)
            }

# Global instance
_shared_manager = None

def get_shared_camera() -> SharedCameraManager:
    """Get the global shared camera manager"""
    global _shared_manager
    if _shared_manager is None:
        _shared_manager = SharedCameraManager()
    return _shared_manager