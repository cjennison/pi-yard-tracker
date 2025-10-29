#!/usr/bin/env python3
"""
Pi Yard Tracker - Camera System Entrypoint

ONLY does:
1. Start SharedCameraManager (camera coordination)
2. Start CameraCapture (save photos + run detections)
3. Start LiveStream WebSocket server

That's it. Database, cleanup, sessions handled elsewhere.
"""

import argparse
import asyncio
import logging
import signal
import sys
import threading
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from backend.shared_camera import SharedCameraManager
from backend.capture.camera_capture import CameraCapture, YOLODetector
from backend.api.live_stream import LiveCameraManager
from backend.api.main import app
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global references for cleanup
shared_camera = None
camera_capture = None
live_manager = None
capture_thread = None
api_server = None
detector = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("\n🛑 Shutdown signal received, cleaning up...")
    cleanup_and_exit()

def cleanup_and_exit():
    """Clean up camera system components"""
    global shared_camera, camera_capture, live_manager
    
    # Stop camera capture
    if camera_capture:
        camera_capture.cleanup()
    
    # LiveCameraManager doesn't have cleanup method - just let it go
    
    # Stop shared camera
    if shared_camera:
        shared_camera.stop()
    
    logger.info("✅ Cleanup complete")
    sys.exit(0)

def capture_loop(camera_capture, detector=None, interval=1.0):
    """Simple photo capture loop with detection"""
    capture_count = 0
    detection_count = 0
    
    try:
        while True:
            # Capture photo
            photo_path = camera_capture.capture()
            
            if photo_path:
                capture_count += 1
                
                # Run detection if detector available
                if detector:
                    detections = detector.detect(photo_path, save_visualization=True)
                    if detections:
                        detection_count += 1
                        logger.info(f"🦌 Found {len(detections)} objects in {photo_path.name}")
                
                # Log every 10 captures
                if capture_count % 10 == 0:
                    logger.info(f"📊 {capture_count} photos, {detection_count} with detections")
            
            time.sleep(interval)
            
    except Exception as e:
        logger.error(f"❌ Capture error: {e}")

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
    global shared_camera, camera_capture, live_manager, capture_thread, detector
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Pi Yard Tracker - Camera System Only')
    parser.add_argument('--no-capture', action='store_true', help='Live stream only')
    parser.add_argument('--capture-only', action='store_true', help='No live stream')
    parser.add_argument('--interval', type=float, default=1.0, help='Capture interval (default: 1.0)')
    parser.add_argument('--port', type=int, default=8001, help='API port (default: 8001)')
    parser.add_argument('--model', type=str, default='models/custom_model/weights/best.pt', help='YOLO model')
    parser.add_argument('--confidence', type=float, default=0.25, help='Detection confidence')
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🐾 Pi Yard Tracker - Camera System")
    logger.info(f"📷 Capture: {'No' if args.no_capture else 'Yes'}")
    logger.info(f"📡 Live stream: {'No' if args.capture_only else 'Yes'}")
    
    try:
        # 1. Start shared camera
        logger.info("🔗 Starting shared camera...")
        shared_camera = SharedCameraManager()
        
        # 2. Start photo capture (if enabled)
        if not args.no_capture:
            logger.info("📷 Starting photo capture...")
            photo_dir = Path("data/photos")
            photo_dir.mkdir(parents=True, exist_ok=True)
            
            camera_capture = CameraCapture(photo_dir=photo_dir)
            
            # Initialize detector
            detector = YOLODetector(model_name=args.model, confidence_threshold=args.confidence)
            
            # Start capture thread
            capture_thread = threading.Thread(
                target=capture_loop,
                args=(camera_capture, detector, args.interval),
                daemon=True
            )
            capture_thread.start()
        
        # 3. Start live stream (if enabled)
        if not args.capture_only:
            logger.info("📡 Starting live stream...")
            live_manager = LiveCameraManager(model_path=args.model)
            app.state.live_manager = live_manager
        
        logger.info(f"🚀 Camera system running on port {args.port}")
        logger.info("Press Ctrl+C to stop")
        
        # 4. Run API server
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