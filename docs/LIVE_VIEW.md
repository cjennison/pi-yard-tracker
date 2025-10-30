# Live Camera View - Technical Details

## Overview

The live camera view provides real-time visualization of what the camera sees and what the AI is detecting, giving you immediate feedback on the system's performance.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Raspberry Pi   │         │   WebSocket      │         │    Browser      │
│                 │         │                  │         │                 │
│  Camera Module  │────────▶│   FastAPI        │────────▶│  React + Canvas │
│     ↓           │  frames │   Server         │  MJPEG  │     ↓           │
│  YOLO Model     │────────▶│                  │────────▶│  Draw Boxes     │
│                 │detection│                  │  JSON   │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

## How It Works (In Simple Terms)

### 1. Camera Captures Frame

- The Pi camera grabs a frame (like taking a photo)
- This happens continuously, creating a video stream

### 2. YOLO Processes Frame

- Each frame is fed through the YOLO neural network
- YOLO outputs: "I see a dog at position X,Y with 85% confidence"
- This takes ~200-500ms on a Raspberry Pi 4

### 3. Frame Encoding

- The frame is converted to JPEG format
- JPEG is compressed so it transfers faster over network
- We use "MJPEG" (Motion JPEG) = series of JPEG images

### 4. WebSocket Transmission

- **Why WebSocket?** Traditional HTTP requires client to ask for each frame
- WebSocket keeps connection open, server pushes frames automatically
- Much more efficient for real-time streaming

### 5. Browser Rendering

- Browser receives JPEG frame + detection data (bounding boxes)
- HTML5 Canvas draws the image
- JavaScript draws colored rectangles (boxes) over detected objects
- Labels and confidence scores added as text

## Implementation Components

### Backend: `backend/stream.py`

```python
class CameraStreamer:
    async def stream_frames(self, websocket):
        """Stream frames with detections to browser"""
        while True:
            # Capture frame
            frame = camera.capture_array()

            # Run detection
            detections = model.detect(frame)

            # Encode as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = base64.b64encode(buffer).decode()

            # Send frame + detections
            await websocket.send_json({
                "frame": frame_bytes,
                "detections": detections,
                "timestamp": time.time()
            })

            await asyncio.sleep(0.1)  # ~10 FPS
```

### Frontend: `frontend/src/components/LiveView.tsx`

```typescript
const LiveView = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const socket = new WebSocket("ws://raspberrypi.local:8000/ws/stream");

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // Draw frame
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      const img = new Image();
      img.src = "data:image/jpeg;base64," + data.frame;
      img.onload = () => ctx.drawImage(img, 0, 0);

      // Draw bounding boxes
      data.detections.forEach((det) => {
        ctx.strokeStyle = "#00ff00";
        ctx.strokeRect(det.x, det.y, det.width, det.height);
        ctx.fillText(`${det.class} ${det.confidence}%`, det.x, det.y);
      });
    };
  }, []);

  return <canvas ref={canvasRef} width={1920} height={1080} />;
};
```

## Performance Optimization

### Why Not Full 30 FPS?

- **30 FPS** = 30 frames per second = video quality
- **YOLO processing**: 200-500ms per frame on Pi 4
- **Maximum possible**: ~2-5 FPS with detection
- **Our target**: 5-10 FPS (good balance)

### Optimization Strategies

1. **Dual Resolution**

   - High-res (1920x1080) for saved photos
   - Low-res (640x480) for live stream
   - Smaller images = faster processing & transmission

2. **Frame Skipping**

   - Process every Nth frame for detection
   - Show all frames but only detect on some
   - Smoother video, same detection rate

3. **JPEG Quality**

   - Use 60-70% quality for streaming
   - Use 95% quality for saved photos
   - Reduces bandwidth by 50%+

4. **Browser-side Caching**
   - Reuse canvas context
   - Batch draw operations
   - Use requestAnimationFrame for smooth rendering

## Network Considerations

### Local Network (Recommended)

- Pi and computer on same WiFi/Ethernet
- Low latency (~10-50ms)
- High bandwidth available
- **Speed**: 5-10 FPS easily achievable

### Remote Access

- VPN or port forwarding required
- Higher latency (50-500ms)
- Limited bandwidth
- **Speed**: 1-3 FPS recommended
- Consider lower resolution (320x240)

## User Controls

### Detection Confidence Threshold

```typescript
// Slider: 0.1 to 0.9
// Higher = fewer false positives, might miss real detections
// Lower = more detections, more false alarms
<Slider
  min={0.1}
  max={0.9}
  value={confidence}
  onChange={(val) => {
    // Send to backend via WebSocket
    ws.send(
      JSON.stringify({
        type: "config",
        confidence: val,
      })
    );
  }}
/>
```

### Visual Toggles

- **Show/Hide Boxes**: Toggle bounding box overlay
- **Show/Hide Labels**: Toggle text labels
- **Show/Hide Confidence**: Toggle confidence percentages
- **Capture Flash**: Visual indicator when photo saved
- **Grid Overlay**: Help align camera view

## Development vs Production

### Development Mode

- Run on laptop/desktop for testing
- Simulate camera with webcam or video file
- Lower latency, easier debugging

### Production Mode

- Run on Raspberry Pi
- Real camera module
- Access via network from any device

## Educational: WebSocket vs HTTP Polling

### HTTP Polling (Old Way)

```javascript
// Browser asks for frame every 100ms
setInterval(() => {
  fetch("/api/current-frame")
    .then((res) => res.json())
    .then((data) => drawFrame(data));
}, 100);

// Problems:
// - Server processes 10 requests/sec even if nothing changed
// - Each request has overhead (headers, handshake)
// - Wasteful of resources
```

### WebSocket (Modern Way)

```javascript
// One connection, server pushes when ready
const ws = new WebSocket("ws://server/stream");
ws.onmessage = (event) => {
  drawFrame(JSON.parse(event.data));
};

// Benefits:
// - Single connection stays open
// - Server pushes only when new frame ready
// - Much lower latency
// - Efficient use of resources
```

## Security Considerations

### Local Network Only (Default)

- WebSocket server binds to local IP only
- Only accessible from same network
- No internet exposure

### If Remote Access Needed

- Use VPN (recommended): WireGuard, Tailscale
- Or use nginx reverse proxy with SSL/TLS
- Add authentication token
- Never expose directly to internet

## Troubleshooting

### "Laggy" Stream

- **Cause**: Network congestion or CPU overload
- **Fix**: Lower resolution, reduce FPS, or improve WiFi

### Boxes Don't Align with Objects

- **Cause**: Resolution mismatch
- **Fix**: Ensure canvas size matches frame size

### No Detections Showing

- **Cause**: Confidence threshold too high
- **Fix**: Lower threshold slider

### Connection Drops

- **Cause**: Pi sleep/power saving or network issue
- **Fix**: Disable WiFi power management, use Ethernet

## What You'll Have

With the live view feature, you'll have:

- ✅ Live camera feed in browser
- ✅ Real-time detection visualization
- ✅ Interactive controls
- ✅ Performance monitoring

This makes debugging and monitoring your yard incredibly easy - you can see exactly what the AI sees and adjust settings in real-time!
