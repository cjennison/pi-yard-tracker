"""
Live camera streaming with WebSocket support for Pi Yard Tracker.

This module provides real-time camera streaming with YOLO object detection overlay.
Designed to work alongside the existing camera capture system using shared resources.
"""

import json
import base64
import time
import asyncio
from datetime import datetime
from io import BytesIO
from typing import List, Dict, Optional

import numpy as np
from PIL import Image
from fastapi import WebSocket, WebSocketDisconnect

# Import detection capabilities
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# Import shared camera manager
from backend.shared_camera import get_shared_camera

import logging

logger = logging.getLogger(__name__)

import asyncio
import json
import time
import base64
import logging
from typing import Dict, List, Optional
from datetime import datetime
from io import BytesIO

from fastapi import WebSocket, WebSocketDisconnect
from PIL import Image
import cv2
import numpy as np

# Import shared camera manager
from backend.shared_camera import get_shared_camera

# Try to import YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

logger = logging.getLogger(__name__)

class LiveCameraManager:
    """
    Manages live camera streaming with detection overlay.
    Uses shared camera resources to work alongside capture system.
    """
    
    def __init__(self, model_path: str = "models/yolov8n.pt"):
        self.model_path = model_path
        self.detector = None
        self.clients: List[WebSocket] = []
        self.confidence_threshold = 0.25
        self.shared_camera = get_shared_camera()
        self.stats = {
            "fps": 0.0,
            "detection_count": 0,
            "processing_time": 0.0,
            "last_detection": None,
            "active_classes": []
        }
        
        # Frame processing
        self.last_frame = None
        self.frame_count = 0
        self.start_time = time.time()
        
        # Initialize YOLO detector
        if YOLO_AVAILABLE:
            try:
                logger.info(f"🤖 Loading YOLO model for live stream: {model_path}")
                self.detector = YOLO(model_path)
                logger.info("✅ Live stream detector ready")
            except Exception as e:
                logger.error(f"❌ Failed to load live stream detector: {e}")
    
    async def add_client(self, websocket: WebSocket):
        """Add a new WebSocket client"""
        await websocket.accept()
        self.clients.append(websocket)
        logger.info(f"📱 Client connected (total: {len(self.clients)})")
        
        # Register stream callback with shared camera if this is first client
        if len(self.clients) == 1:
            self.shared_camera.register_stream_callback(self._on_frame_received)
            if not self.shared_camera.is_started:
                self.shared_camera.start()
    
    async def remove_client(self, websocket: WebSocket):
        """Remove a WebSocket client"""
        if websocket in self.clients:
            self.clients.remove(websocket)
            logger.info(f"📱 Client disconnected (total: {len(self.clients)})")
        
        # Unregister callback if no clients remain
        if len(self.clients) == 0:
            self.shared_camera.remove_stream_callback(self._on_frame_received)
    
    def _on_frame_received(self, frame: np.ndarray, frame_type: str):
        """Callback for when shared camera provides a new frame"""
        if frame_type != "stream" or len(self.clients) == 0:
            return
        
        try:
            # Process frame
            frame_start = time.time()
            
            # Run detection
            detections = self._detect_objects(frame) if self.detector else []
            
            # Calculate processing time
            processing_time = (time.time() - frame_start) * 1000
            
            # Update stats
            self.frame_count += 1
            elapsed = time.time() - self.start_time
            if elapsed >= 1.0:  # Update FPS every second
                self.stats["fps"] = self.frame_count / elapsed
                self.frame_count = 0
                self.start_time = time.time()
            
            self.stats["processing_time"] = processing_time
            if detections:
                self.stats["detection_count"] += len(detections)
                self.stats["last_detection"] = datetime.now().isoformat()
                self.stats["active_classes"] = list(set([d["class_name"] for d in detections]))
            
            # Encode frame as JPEG
            frame_jpg = self._encode_frame(frame)
            if frame_jpg:
                # Send to all connected clients
                message = {
                    "type": "frame",
                    "image": base64.b64encode(frame_jpg).decode('utf-8'),
                    "detections": detections,
                    "stats": self.stats.copy(),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Use asyncio to send to all clients
                asyncio.run_coroutine_threadsafe(
                    self._broadcast_message(message),
                    asyncio.get_event_loop()
                )
                
        except Exception as e:
            logger.debug(f"⚠️  Frame processing error: {e}")
    
    def _detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """Run YOLO detection on frame"""
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
            
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = self.detector.names[class_id]
                confidence = float(box.conf[0])
                
                # Get bounding box coordinates (already in pixels)
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                # Calculate normalized coordinates
                height, width = frame.shape[:2]
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
    
    def _encode_frame(self, frame: np.ndarray) -> Optional[bytes]:
        """Encode frame as JPEG bytes"""
        try:
            # Convert to PIL Image (frame is already RGB from shared camera)
            pil_image = Image.fromarray(frame)
            
            # Encode as JPEG
            buffer = BytesIO()
            pil_image.save(buffer, format='JPEG', quality=85, optimize=True)
            return buffer.getvalue()
            
        except Exception as e:
            logger.debug(f"⚠️  Frame encoding error: {e}")
            return None
    
    async def _broadcast_message(self, message: Dict):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
        
        # Send to all clients, removing disconnected ones
        disconnected = []
        for client in self.clients[:]:  # Copy list to avoid modification during iteration
            try:
                await client.send_text(json.dumps(message))
            except WebSocketDisconnect:
                disconnected.append(client)
            except Exception as e:
                logger.debug(f"⚠️  Error sending to client: {e}")
                disconnected.append(client)
        
        # Remove disconnected clients
        for client in disconnected:
            await self.remove_client(client)
    
    def update_confidence_threshold(self, threshold: float):
        """Update detection confidence threshold"""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        logger.info(f"🎯 Updated live stream confidence threshold: {self.confidence_threshold}")
    
    def get_stats(self) -> Dict:
        """Get current streaming statistics"""
        return self.stats.copy()


# Global instance (singleton pattern)
_live_manager: Optional[LiveCameraManager] = None

def get_live_manager() -> LiveCameraManager:
    """Get or create the global live camera manager"""
    global _live_manager
    if _live_manager is None:
        _live_manager = LiveCameraManager()
    return _live_manager

async def handle_websocket(websocket: WebSocket):
    """Handle WebSocket connection for live camera feed"""
    manager = get_live_manager()
    
    try:
        await manager.add_client(websocket)
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (e.g., configuration updates)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                data = json.loads(message)
                
                # Handle configuration updates
                if data.get("type") == "config":
                    if "confidence_threshold" in data:
                        threshold = float(data["confidence_threshold"]) / 100.0  # Convert percentage
                        manager.update_confidence_threshold(threshold)
                        
            except asyncio.TimeoutError:
                # No message received, continue
                continue
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.debug(f"⚠️  WebSocket message error: {e}")
                break
                
    except Exception as e:
        logger.error(f"❌ WebSocket handler error: {e}")
    finally:
        await manager.remove_client(websocket)