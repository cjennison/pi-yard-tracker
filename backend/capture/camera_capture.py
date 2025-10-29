# Phase 2A: Camera Capture with Object Detection
# 
# This script captures photos from the Raspberry Pi camera every 1 second,
# runs YOLO detection on each photo, and automatically deletes old photos.
#
# Educational Notes:
# - picamera2 is the new official library for Raspberry Pi cameras
# - YOLO (YOLOv8n) runs object detection on each captured photo
# - We use threading to run cleanup independently from capture
# - Photos are captured regardless of detections (data collection)
# - Detection results are logged and can be saved to database later

import time
import os
from pathlib import Path
from datetime import datetime, timedelta
import threading
import logging
import argparse

# Try to import picamera2, but allow running without it for development
try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    print("⚠️  picamera2 not available - running in simulation mode")

# Try to import YOLO, but allow running without it
try:
    from ultralytics import YOLO
    import cv2
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  YOLO not available - run without detection or install: pip install ultralytics opencv-python")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PHOTO_DIR = Path("data/photos")
CAPTURE_INTERVAL = 1  # seconds
RETENTION_MINUTES = 15
CLEANUP_INTERVAL = 30  # seconds - how often to check for old files
DETECTION_ENABLED = True  # Set to False to disable YOLO detection
CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for detections (0.0-1.0)
SAVE_DETECTIONS = True  # Save images with bounding boxes drawn

class CameraCapture:
    """Handles camera initialization and photo capture"""
    
    def __init__(self, photo_dir: Path, simulate: bool = False):
        self.photo_dir = photo_dir
        self.simulate = simulate
        self.camera = None
        
        # Create photo directory if it doesn't exist
        self.photo_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Photo directory: {self.photo_dir.absolute()}")
        
        # Initialize camera
        if not simulate and CAMERA_AVAILABLE:
            self._init_camera()
        else:
            logger.warning("🎭 Running in SIMULATION mode (no actual camera)")
    
    def _init_camera(self):
        """Initialize the Raspberry Pi camera"""
        try:
            self.camera = Picamera2()
            
            # Configure camera for still capture
            config = self.camera.create_still_configuration(
                main={"size": (1920, 1080)},  # Full HD
                lores={"size": (640, 480)},   # Lower res for preview
                display="lores"
            )
            self.camera.configure(config)
            self.camera.start()
            
            # Give camera time to adjust to lighting
            time.sleep(2)
            logger.info("📷 Camera initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize camera: {e}")
            self.simulate = True
            logger.warning("🎭 Falling back to SIMULATION mode")
    
    def capture(self) -> Path:
        """Capture a single photo and return its path"""
        # Generate filename with timestamp
        timestamp = datetime.now()
        filename = f"yard_{timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.jpg"
        filepath = self.photo_dir / filename
        
        if self.camera and not self.simulate:
            # Actual camera capture
            try:
                self.camera.capture_file(str(filepath))
                logger.info(f"📸 Captured: {filename}")
            except Exception as e:
                logger.error(f"❌ Capture failed: {e}")
                return None
        else:
            # Simulation mode - create a dummy file
            filepath.touch()
            logger.info(f"🎭 Simulated: {filename}")
        
        return filepath
    
    def cleanup(self):
        """Stop the camera and cleanup resources"""
        if self.camera:
            self.camera.stop()
            logger.info("📷 Camera stopped")


class YOLODetector:
    """Handles object detection using YOLO model"""
    
    def __init__(self, model_name='yolov8n.pt', confidence_threshold=0.5):
        """Initialize YOLO detector"""
        self.confidence_threshold = confidence_threshold
        # If model_name is already a path, use it directly; otherwise prepend 'models/'
        model_path_input = Path(model_name)
        if model_path_input.is_absolute() or str(model_name).startswith('models/'):
            self.model_path = model_path_input
        else:
            self.model_path = Path('models') / model_name
        self.model = None
        
        if not YOLO_AVAILABLE:
            logger.warning("⚠️  YOLO not available - detection disabled")
            return
        
        logger.info(f"🤖 Initializing YOLO detector...")
        logger.info(f"📊 Confidence threshold: {confidence_threshold}")
        
        try:
            # Create models directory
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📦 Loading model: {self.model_path.name}")
            self.model = YOLO(str(self.model_path))
            self.class_names = self.model.names
            
            logger.info(f"✅ Model loaded successfully")
            logger.info(f"📋 Model can detect {len(self.class_names)} object classes")
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            self.model = None
    
    def detect(self, image_path, save_visualization=False):
        """
        Detect objects in an image
        
        Returns:
            List of detections with class, confidence, and bbox
        """
        if not self.model:
            return []
        
        image_path = Path(image_path)
        if not image_path.exists():
            return []
        
        try:
            # Run detection
            start_time = time.time()
            results = self.model.predict(
                source=str(image_path),
                conf=self.confidence_threshold,
                verbose=False
            )
            inference_time = (time.time() - start_time) * 1000
            
            # Parse results
            detections = []
            result = results[0]
            
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = self.class_names[class_id]
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()
                
                detections.append({
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': bbox
                })
            
            # Log results
            if detections:
                logger.info(f"🔍 Detected {len(detections)} object(s) ({inference_time:.0f}ms)")
                for det in detections:
                    logger.info(f"   🐾 {det['class']}: {det['confidence']:.2%}")
                
                # Save visualization if requested
                if save_visualization:
                    self._save_visualization(image_path, detections)
            else:
                logger.debug(f"🔍 No objects detected ({inference_time:.0f}ms)")
            
            return detections
            
        except Exception as e:
            logger.error(f"❌ Detection failed: {e}")
            return []
    
    def _save_visualization(self, image_path, detections):
        """Draw bounding boxes on image and save"""
        try:
            image = cv2.imread(str(image_path))
            
            for det in detections:
                x1, y1, x2, y2 = [int(coord) for coord in det['bbox']]
                class_name = det['class']
                confidence = det['confidence']
                
                # Draw rectangle
                color = (0, 255, 0)
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{class_name} {confidence:.2%}"
                font = cv2.FONT_HERSHEY_SIMPLEX
                (text_width, text_height), _ = cv2.getTextSize(label, font, 0.6, 2)
                
                cv2.rectangle(image, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
                cv2.putText(image, label, (x1, y1 - 5), font, 0.6, (0, 0, 0), 2)
            
            # Save to detections subfolder
            output_dir = image_path.parent / 'detections'
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"detected_{image_path.name}"
            
            cv2.imwrite(str(output_path), image)
            logger.debug(f"💾 Saved visualization: {output_path.name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save visualization: {e}")

class PhotoCleanup:
    """Handles automatic deletion of old photos"""
    
    def __init__(self, photo_dir: Path, retention_minutes: int):
        self.photo_dir = photo_dir
        self.retention_minutes = retention_minutes
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the cleanup thread"""
        self.running = True
        self.thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.thread.start()
        logger.info(f"🧹 Cleanup service started (retention: {self.retention_minutes} minutes)")
    
    def stop(self):
        """Stop the cleanup thread"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("🧹 Cleanup service stopped")
    
    def _cleanup_loop(self):
        """Continuously check and delete old photos"""
        while self.running:
            self._delete_old_photos()
            time.sleep(CLEANUP_INTERVAL)
    
    def _delete_old_photos(self):
        """Delete photos older than retention period"""
        cutoff_time = datetime.now() - timedelta(minutes=self.retention_minutes)
        deleted_count = 0
        
        # Find all .jpg files in photo directory
        for photo_path in self.photo_dir.glob("*.jpg"):
            # Get file modification time
            file_time = datetime.fromtimestamp(photo_path.stat().st_mtime)
            
            # Delete if older than cutoff
            if file_time < cutoff_time:
                try:
                    photo_path.unlink()
                    deleted_count += 1
                    logger.debug(f"🗑️  Deleted old photo: {photo_path.name}")
                except Exception as e:
                    logger.error(f"❌ Failed to delete {photo_path.name}: {e}")
        
        if deleted_count > 0:
            logger.info(f"🗑️  Deleted {deleted_count} old photo(s)")

def main():
    """Main application loop"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Pi Yard Tracker - Camera Capture with Object Detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default pre-trained model (YOLOv8n - 80 classes)
  python backend/capture/camera_capture.py
  
  # Use custom trained model
  python backend/capture/camera_capture.py --model models/custom_model/weights/best.pt
  
  # Adjust confidence threshold
  python backend/capture/camera_capture.py --model models/custom_model/weights/best.pt --confidence 0.3
        """
    )
    parser.add_argument('--model', type=str, default='yolov8n.pt',
                        help='Path to YOLO model (default: yolov8n.pt)')
    parser.add_argument('--confidence', type=float, default=CONFIDENCE_THRESHOLD,
                        help=f'Confidence threshold for detections (default: {CONFIDENCE_THRESHOLD})')
    parser.add_argument('--no-detection', action='store_true',
                        help='Disable object detection (capture only)')
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🐾 Pi Yard Tracker - Phase 2A: Camera + Detection")
    logger.info("=" * 60)
    logger.info(f"⏱️  Capture interval: {CAPTURE_INTERVAL} second(s)")
    logger.info(f"🕐 Retention period: {RETENTION_MINUTES} minutes")
    logger.info(f"🤖 Detection: {'Enabled' if DETECTION_ENABLED and YOLO_AVAILABLE and not args.no_detection else 'Disabled'}")
    if not args.no_detection and YOLO_AVAILABLE:
        logger.info(f"📦 Model: {args.model}")
        logger.info(f"📊 Confidence: {args.confidence}")
    logger.info("=" * 60)
    
    # Check if we should simulate
    simulate = not CAMERA_AVAILABLE or os.getenv('SIMULATE_CAMERA', '').lower() == 'true'
    
    # Initialize components
    camera = CameraCapture(PHOTO_DIR, simulate=simulate)
    cleanup = PhotoCleanup(PHOTO_DIR, RETENTION_MINUTES)
    
    # Initialize detector if enabled
    detector = None
    if DETECTION_ENABLED and YOLO_AVAILABLE and not args.no_detection:
        try:
            detector = YOLODetector(model_name=args.model, confidence_threshold=args.confidence)
        except Exception as e:
            logger.error(f"❌ Failed to initialize detector: {e}")
            logger.warning("⚠️  Continuing without detection")
    
    # Start cleanup service
    cleanup.start()
    
    try:
        logger.info("🚀 Starting capture loop (Press Ctrl+C to stop)")
        logger.info("")
        
        capture_count = 0
        detection_count = 0
        
        while True:
            # Capture photo (always happens)
            photo_path = camera.capture()
            
            if photo_path:
                capture_count += 1
                
                # Run detection if enabled
                if detector:
                    detections = detector.detect(photo_path, save_visualization=SAVE_DETECTIONS)
                    if detections:
                        detection_count += 1
            
            # Show stats every 10 captures
            if capture_count % 10 == 0:
                photo_count = len(list(PHOTO_DIR.glob("*.jpg")))
                if detector:
                    logger.info(f"📊 Stats: {capture_count} captured, {detection_count} with detections, {photo_count} stored")
                else:
                    logger.info(f"📊 Stats: {capture_count} captured, {photo_count} stored")
            
            # Wait for next capture
            time.sleep(CAPTURE_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("")
        logger.info("⏸️  Shutting down...")
    finally:
        # Cleanup
        cleanup.stop()
        camera.cleanup()
        
        # Final stats
        photo_count = len(list(PHOTO_DIR.glob("*.jpg")))
        if detector:
            logger.info(f"📊 Final stats: {capture_count} total captures, {detection_count} with detections, {photo_count} photos remaining")
        else:
            logger.info(f"📊 Final stats: {capture_count} total captures, {photo_count} photos remaining")
        logger.info("👋 Goodbye!")

if __name__ == "__main__":
    main()
