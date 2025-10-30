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
from backend.capture.photo_capture import PhotoCaptureService
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
live_manager = None
photo_capture_service = None
cleanup_service = None
cleanup_thread = None
api_server = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("\n🛑 Shutdown signal received, cleaning up...")
    cleanup_and_exit()

def cleanup_and_exit():
    """Clean up camera system components"""
    global shared_camera, live_manager, photo_capture_service, cleanup_service
    
    # Stop photo capture service
    if photo_capture_service:
        photo_capture_service.stop()
    
    # Stop cleanup service
    if cleanup_service:
        cleanup_service.stop()
    
    # Stop shared camera
    if shared_camera:
        shared_camera.stop()
    
    logger.info("✅ Cleanup complete")
    sys.exit(0)

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
    global shared_camera, live_manager, photo_capture_service, cleanup_service, cleanup_thread
    
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
            
            # Create and start photo capture service
            photo_capture_service = PhotoCaptureService(
                shared_camera=shared_camera,
                photo_dir=photo_dir,
                detector=detector,
                interval=args.interval,
                model_name=args.model,
                confidence=args.confidence
            )
            photo_capture_service.start()
        
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