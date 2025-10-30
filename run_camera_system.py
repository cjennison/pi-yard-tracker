#!/usr/bin/env python3
"""
Pi Yard Tracker - Camera System Entrypoint

Complete system:
1. Start SharedCameraManager (camera coordination)
2. Start CameraCapture (save photos + run detections + save to database)
3. Start LiveStream WebSocket server
4. Run FastAPI server
"""

import argparse
import asyncio
import logging
import signal
import sys
import threading
import time
from pathlib import Path
from datetime import datetime
from PIL import Image

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from backend.shared_camera import SharedCameraManager
from backend.detection.detector import YOLODetector
from backend.api.live_stream import LiveCameraManager
from backend.api.main import app
from backend.cleanup_service import PhotoCleanupService
import uvicorn

# Database imports
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global references for cleanup
shared_camera = None
live_manager = None
capture_thread = None
cleanup_service = None
cleanup_thread = None
api_server = None
detector = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("\n🛑 Shutdown signal received, cleaning up...")
    cleanup_and_exit()

def cleanup_and_exit():
    """Clean up camera system components"""
    global shared_camera, live_manager, cleanup_service
    
    # Stop cleanup service
    if cleanup_service:
        cleanup_service.stop()
    
    # Stop shared camera
    if shared_camera:
        shared_camera.stop()
    
    logger.info("✅ Cleanup complete")
    sys.exit(0)

def capture_loop(photo_dir, detector=None, interval=1.0, model_name=None, confidence=0.25):
    """Photo capture loop with database integration"""
    global shared_camera
    
    capture_count = 0
    detection_count = 0
    session_id = None
    last_capture_time = 0
    
    # Create database session if available
    if DATABASE_AVAILABLE and detector:
        try:
            session_id = create_session(
                model_name=model_name,
                confidence_threshold=confidence
            )
            logger.info(f"🎬 Created database session {session_id}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to create database session: {e}")
    
    def handle_frame(frame, frame_type):
        """Callback to handle captured frames"""
        nonlocal capture_count, detection_count, last_capture_time
        
        # Only process capture frames (not stream frames)
        if frame_type != "capture":
            return
        
        # Respect the interval setting
        current_time = time.time()
        if current_time - last_capture_time < interval:
            return
        
        last_capture_time = current_time
        
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"photo_{timestamp}.jpg"
            photo_path = photo_dir / filename
            
            # Save frame as JPEG
            img = Image.fromarray(frame)
            img.save(photo_path, 'JPEG', quality=95)
            
            capture_count += 1
            photo_id = None
            
            # Save photo to database
            if DATABASE_AVAILABLE:
                try:
                    # Get image dimensions
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
            if detector:
                detections = detector.detect(photo_path, save_visualization=True)
                if detections:
                    detection_count += 1
                    logger.info(f"🦌 Found {len(detections)} objects in {filename}")
                    
                    # Save detections to database
                    if DATABASE_AVAILABLE and photo_id:
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
                                    model_name=model_name
                                )
                            
                            # Update photo detection count
                            update_photo_detections(photo_id, len(detections))
                            logger.debug(f"💾 Saved {len(detections)} detections to database")
                        except Exception as e:
                            logger.warning(f"⚠️  Failed to save detections to database: {e}")
            
            # Log every 10 captures
            if capture_count % 10 == 0:
                logger.info(f"📊 {capture_count} photos, {detection_count} with detections")
        
        except Exception as e:
            logger.error(f"❌ Error processing frame: {e}")
    
    # Register callback with shared camera
    shared_camera.register_capture_callback(handle_frame)
    
    try:
        # Wait for shutdown signal
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("⏸️  Capture loop interrupted")
    finally:
        # Cleanup: unregister callback
        shared_camera.remove_capture_callback(handle_frame)
        
        # End database session when loop exits
        if DATABASE_AVAILABLE and session_id:
            try:
                end_session(session_id, capture_count, detection_count)
                logger.info(f"🎬 Ended database session {session_id}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to end database session: {e}")

async def run_api_server(host="0.0.0.0", port=8000):
    """Run the FastAPI server"""
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    # Store server reference for cleanup
    global api_server
    api_server = server
    
    await server.serve()

def main():
    """Main entrypoint - ONLY camera system"""
    global shared_camera, camera_capture, live_manager, capture_thread, detector, cleanup_service, cleanup_thread
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Pi Yard Tracker - Complete Camera System')
    parser.add_argument('--no-capture', action='store_true', help='Live stream only')
    parser.add_argument('--capture-only', action='store_true', help='No live stream')
    parser.add_argument('--interval', type=float, default=10.0, help='Capture interval in seconds (default: 10.0)')
    parser.add_argument('--port', type=int, default=8000, help='API port (default: 8000)')
    parser.add_argument('--model', type=str, default='models/custom_model/weights/best.pt', help='YOLO model')
    parser.add_argument('--confidence', type=float, default=0.25, help='Detection confidence')
    parser.add_argument('--retention-hours', type=int, default=1, help='Photo retention in hours (default: 1)')
    parser.add_argument('--cleanup-interval', type=int, default=300, help='Cleanup check interval in seconds (default: 300)')
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🐾 Pi Yard Tracker - Camera System")
    logger.info(f"📷 Capture: {'No' if args.no_capture else 'Yes'}")
    logger.info(f"📡 Live stream: {'No' if args.capture_only else 'Yes'}")
    logger.info(f"💾 Database: {'Enabled' if DATABASE_AVAILABLE else 'Disabled'}")
    if not args.no_capture:
        logger.info(f"📦 Model: {args.model}")
        logger.info(f"📊 Confidence: {args.confidence}")
        logger.info(f"⏱️  Interval: {args.interval}s")
    
    try:
        # 1. Start shared camera
        logger.info("🔗 Starting shared camera...")
        shared_camera = SharedCameraManager()
        shared_camera.start()  # Start the camera immediately
        
        # 2. Start cleanup service
        logger.info("🧹 Starting cleanup service...")
        photo_dir = Path("data/photos")
        cleanup_service = PhotoCleanupService(
            photo_dir=photo_dir,
            retention_hours=args.retention_hours,
            check_interval=args.cleanup_interval
        )
        cleanup_thread = threading.Thread(target=cleanup_service.start, daemon=True)
        cleanup_thread.start()
        
        # 3. Start photo capture (if enabled)
        if not args.no_capture:
            logger.info("📷 Starting photo capture...")
            photo_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize detector
            detector = YOLODetector(model_name=args.model, confidence_threshold=args.confidence)
            
            # Start capture thread
            capture_thread = threading.Thread(
                target=capture_loop,
                args=(photo_dir, detector, args.interval, args.model, args.confidence),
                daemon=True
            )
            capture_thread.start()
        
        # 4. Start live stream (if enabled)
        if not args.capture_only:
            logger.info("📡 Starting live stream...")
            live_manager = LiveCameraManager(model_path=args.model)
            app.state.live_manager = live_manager
        
        logger.info(f"🚀 Camera system running on port {args.port}")
        logger.info("Press Ctrl+C to stop")
        
        # 5. Run API server
        if not args.capture_only:
            asyncio.run(run_api_server(port=args.port))
        else:
            # Capture-only - just wait
            while True:
                time.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("⏸️  Stopping...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        cleanup_and_exit()

if __name__ == "__main__":
    main()