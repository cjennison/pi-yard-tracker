# How to modify camera_capture.py to work with shared camera (MINIMAL CHANGES)

# OLD CODE (around line 70-80):
class CameraCapture:
    def __init__(self, photo_dir: Path, simulate: bool = False):
        self.photo_dir = photo_dir
        self.simulate = simulate
        self.camera = None
        
        if not simulate and CAMERA_AVAILABLE:
            self._init_camera()

# NEW CODE (replace the class with this):
class CameraCapture:
    def __init__(self, photo_dir: Path, simulate: bool = False):
        self.photo_dir = photo_dir
        self.simulate = simulate
        self.camera = None
        self.shared_camera = None
        self.capture_buffer = None
        self.capture_ready = threading.Event()
        
        # Create photo directory
        self.photo_dir.mkdir(parents=True, exist_ok=True)
        
        if not simulate:
            # Use shared camera instead of direct camera control
            from backend.shared_camera import get_shared_camera
            self.shared_camera = get_shared_camera()
            self.shared_camera.register_capture_callback(self._on_frame_received)
            if not self.shared_camera.is_started:
                self.shared_camera.start()
            logger.info("📷 Using shared camera system")
        else:
            logger.warning("🎭 Running in SIMULATION mode")
    
    def _on_frame_received(self, frame, frame_type):
        """Callback when shared camera provides a frame"""
        if frame_type == "capture":
            self.capture_buffer = frame.copy()
            self.capture_ready.set()
    
    def capture(self) -> Path:
        """Capture a single photo and return its path"""
        timestamp = datetime.now()
        filename = f"capture_{timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.jpg"
        filepath = self.photo_dir / filename
        
        if self.shared_camera and not self.simulate:
            try:
                # Wait for next frame from shared camera
                self.capture_ready.clear()
                if self.capture_ready.wait(timeout=5.0):
                    if self.capture_buffer is not None:
                        pil_image = Image.fromarray(self.capture_buffer)
                        pil_image.save(filepath, 'JPEG', quality=95)
                        logger.info(f"📸 Captured: {filename}")
                        return filepath
                else:
                    logger.error("❌ Timeout waiting for camera frame")
                    return None
            except Exception as e:
                logger.error(f"❌ Capture failed: {e}")
                return None
        else:
            # Simulation mode - create dummy file
            filepath.touch()
            logger.info(f"🎭 Simulated: {filename}")
        
        return filepath
    
    def cleanup(self):
        """Stop the camera and cleanup resources"""
        if self.shared_camera:
            self.shared_camera.remove_capture_callback(self._on_frame_received)
            logger.info("📷 Camera capture cleanup complete")

# The rest of camera_capture.py remains EXACTLY the same!
# - YOLODetector class unchanged
# - Database integration unchanged  
# - Main loop unchanged
# - CLI arguments unchanged