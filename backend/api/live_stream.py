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
from typing import List, Dict, Optional

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

# Import shared camera manager
from backend.shared_camera import get_shared_camera

# Import detection and encoding
from backend.detection.live_detection import LiveDetector
from backend.api.frame_encoder import FrameEncoder

import logging

logger = logging.getLogger(__name__)

class LiveCameraManager:
    """
    Manages live camera streaming with detection overlay.
    Uses shared camera resources to work alongside capture system.
    """
    
    def __init__(self, model_path: str = "models/custom_model/weights/best.pt"):
        self.model_path = model_path
        self.clients: List[WebSocket] = []
        self.shared_camera = get_shared_camera()
        self.loop = None  # Will be set when first client connects
        
        # Initialize detector and encoder
        self.detector = LiveDetector(model_path)
        self.encoder = FrameEncoder(format='JPEG', quality=85)
        
        # Stats tracking
        self.stats = {
            "fps": 0.0,
            "detection_count": 0,
            "processing_time": 0.0,
            "last_detection": None,
            "active_classes": []
        }
        
        # Frame processing
        self.frame_count = 0
        self.start_time = time.time()
    
    async def add_client(self, websocket: WebSocket):
        """Add a new WebSocket client"""
        await websocket.accept()
        self.clients.append(websocket)
        logger.info(f"📱 Client connected (total: {len(self.clients)})")
        
        # Store event loop reference if not already set
        if self.loop is None:
            self.loop = asyncio.get_event_loop()
        
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
            detections = self.detector.detect(frame)
            
            # Calculate processing time
            processing_time = (time.time() - frame_start) * 1000
            
            # Update stats
            self._update_stats(processing_time, detections)
            
            # Encode frame as JPEG
            frame_jpg = self.encoder.encode(frame)
            if frame_jpg:
                # Send to all connected clients
                message = {
                    "type": "frame",
                    "image": base64.b64encode(frame_jpg).decode('utf-8'),
                    "detections": detections,
                    "stats": self.stats.copy(),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Use asyncio to send to all clients (only if we have an event loop)
                if self.loop is not None:
                    asyncio.run_coroutine_threadsafe(
                        self._broadcast_message(message),
                        self.loop
                    )
                
        except Exception as e:
            logger.debug(f"⚠️  Frame processing error: {e}")
    
    def _update_stats(self, processing_time: float, detections: List[Dict]):
        """Update streaming statistics"""
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        
        # Update FPS every second
        if elapsed >= 1.0:
            self.stats["fps"] = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = time.time()
        
        self.stats["processing_time"] = processing_time
        
        if detections:
            self.stats["detection_count"] += len(detections)
            self.stats["last_detection"] = datetime.now().isoformat()
            self.stats["active_classes"] = list(set([d["class_name"] for d in detections]))
    
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
        self.detector.update_confidence_threshold(threshold)
    
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

async def handle_websocket(websocket: WebSocket, app_state=None):
    """Handle WebSocket connection for live camera feed"""
    # Use LiveCameraManager from app.state if available (set by run_camera_system.py)
    # Otherwise fall back to singleton (for standalone API server)
    if app_state and hasattr(app_state, 'live_manager'):
        manager = app_state.live_manager
    else:
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