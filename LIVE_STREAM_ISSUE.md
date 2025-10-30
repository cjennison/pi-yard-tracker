# Live View Not Working - Here's Why

## Current Problem

You're running:

```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

This ONLY runs the API server. It does NOT run:

- ❌ Camera capture system
- ❌ Shared camera manager
- ❌ Live streaming feed

The LiveView page connects but shows placeholder/fake data because nothing is feeding actual camera frames to the WebSocket.

## How the System Should Work

```
┌─────────────────────────────────────────────────────────────┐
│                     run_camera_system.py                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐                                         │
│  │ SharedCamera    │  ← Single camera instance               │
│  │ Manager         │                                          │
│  └────┬────────┬───┘                                          │
│       │        │                                              │
│       │        └──────┐                                       │
│       │               │                                       │
│  ┌────▼─────┐   ┌────▼──────────┐                           │
│  │ Camera   │   │ Live Stream   │                            │
│  │ Capture  │   │ Manager       │                            │
│  │          │   │               │                            │
│  │ • Photos │   │ • WebSocket   │                            │
│  │ • YOLO   │   │ • YOLO        │                            │
│  │ • DB     │   │ • Real-time   │                            │
│  └──────────┘   └───────┬───────┘                            │
│                         │                                    │
│                    ┌────▼────────┐                           │
│                    │  FastAPI    │                            │
│                    │  /live WS   │                            │
│                    └─────────────┘                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    Frontend LiveView
```

## Solution: Use the Correct Startup Command

### Option 1: Use the startup script (RECOMMENDED)

```bash
cd /home/cjennison/src/pi-yard-tracker
./start_system.sh
```

This starts everything in one command.

### Option 2: Run manually

```bash
cd /home/cjennison/src/pi-yard-tracker
source venv/bin/activate
python run_camera_system.py --port 8000
```

### Stop Current Processes First

```bash
# Kill the standalone API server
pkill -f "uvicorn backend.api.main"

# Kill any old camera systems
pkill -f "run_camera_system"
```

## What run_camera_system.py Does

1. **Starts SharedCameraManager** - Manages physical camera
2. **Starts CameraCapture thread** - Captures photos every 1s, runs YOLO, saves to DB
3. **Starts LiveCameraManager** - Streams to WebSocket with detections
4. **Starts FastAPI server** - Serves both REST API and WebSocket `/live`

All running on port 8000 (or custom port with `--port`).

## Verify It's Working

### 1. Check processes

```bash
ps aux | grep run_camera
```

Should show Python process running `run_camera_system.py`.

### 2. Check API

```bash
curl http://localhost:8000/health
```

Should return healthy status.

### 3. Check WebSocket (from browser console)

```javascript
const ws = new WebSocket("ws://192.168.40.204:8000/live");
ws.onmessage = (e) => console.log("Frame received:", JSON.parse(e.data));
```

Should see frame messages with detections and stats.

### 4. Check database

```bash
curl http://localhost:8000/stats
```

Should show increasing photo counts as capture runs.

## Frontend Access

- **From Pi**: http://localhost:5173
- **From Desktop**: http://192.168.40.204:5173 (or whatever port Vite shows)

The frontend now auto-detects the correct WebSocket URL:

- Localhost → `ws://localhost:8000/live`
- Remote → `ws://192.168.40.204:8000/live`

## Current Status

**API Server**: ✅ Running (port 8000)
**Camera System**: ❌ NOT running
**Live Stream**: ❌ NOT working (no camera feed)
**Photo Capture**: ❌ NOT running (no new photos in DB)

**Fix**: Run `./start_system.sh` to start everything properly!
