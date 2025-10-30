# Pi Yard Tracker - Project Plan

## Overview

A local-first wildlife monitoring system that captures photos, identifies animals using on-device AI, and provides a web interface to visualize animal activity in your yard.

## Technology Stack

### Backend (Python)

- **picamera2**: Raspberry Pi camera control
- **YOLO (You Only Look Once)**: Lightweight object detection model
  - Specifically: YOLOv8n (nano) or YOLOv5s for low-resource devices
  - Pre-trained on COCO dataset (includes 80 classes: people, dogs, cats, birds, etc.)
- **SQLite**: Lightweight database for metadata storage
- **FastAPI**: REST API for web interface communication
- **OpenCV**: Image processing utilities
- **WebSockets**: Real-time camera feed and detection streaming

### Frontend (React + Mantine)

- **React 18**: UI framework
- **Mantine v7**: Component library (modern, accessible, easy to use)
- **Recharts**: Timeline visualization
- **Axios**: API communication
- **WebSocket**: Real-time camera feed and detection updates

### Why This Stack?

1. **YOLO**: Industry standard for real-time object detection, runs efficiently on Raspberry Pi 4/5
2. **Python**: Excellent ML/AI library support, native camera integration
3. **SQLite**: No server needed, fast for read-heavy workloads
4. **FastAPI**: Fast, modern Python web framework with automatic API docs
5. **Mantine**: Beautiful components out-of-the-box, excellent documentation

## Educational Notes

### How YOLO Works

- **YOLO (You Only Look Once)** divides images into a grid and predicts bounding boxes and class probabilities simultaneously
- Unlike older methods that scan images multiple times, YOLO looks "once" - making it fast enough for real-time use
- Pre-trained models can detect common animals (dogs, cats, birds, horses, sheep, cows, etc.) without additional training
- Runs on CPU but benefits from GPU acceleration if available

### Hardware-AI Interaction

- The camera captures raw frames → OpenCV processes them → YOLO analyzes for objects → Results stored in SQLite
- Trade-off: Smaller models (YOLOv8n) = faster inference but less accurate; Larger models = more accurate but slower
- Raspberry Pi 4/5 can process ~2-5 FPS with YOLOv8n, perfect for wildlife monitoring

## System Components

### Component 1: Camera Capture & Basic Storage ✅

**Goal**: Get camera working, capture photos, implement auto-deletion

**Deliverables**:

- Python script that captures photos every 1 second
- Stores photos with timestamp in filename
- Auto-deletes photos older than 15 minutes
- Basic logging to console

**Testing**: Run script, verify photos are created and deleted properly

**Duration**: ~1-2 hours to implement and test

---

### Component 2: Object Detection - Pre-trained Model ✅

**Goal**: Add YOLO model to detect common animals/people

**Deliverables**:

- Download and setup YOLOv8n pre-trained model (~6MB)
- Process each captured image for detections
- Detect common animals: dog, cat, bird, horse, bear, person
- Store detection metadata (timestamp, detected objects, confidence scores)
- SQLite database schema created
- Console output showing what was detected
- Visual detection: save images with bounding boxes drawn

**Testing**: Point camera at objects/pets, verify detections are accurate

**Duration**: ~2-3 hours to implement and test

**Educational Value:**

- Learn how pre-trained models work
- Understand confidence scores and thresholds
- See YOLO in action immediately

---

### Component 3: Custom Model Training (OPTIONAL)

**Goal**: Train custom model for specific animals (deer, turkey, etc.)

**Deliverables**:

- Image annotation tool integration (LabelImg)
- Dataset preparation scripts
- Training script (runs on laptop/desktop)
- Model evaluation and testing
- Instructions for deploying custom model to Pi
- Support for custom animal classes

**Testing**: Train on deer dataset, verify model detects deer accurately

**Duration**: ~6-10 hours (mostly annotation time)

**Educational Value:**

- Learn transfer learning concepts
- Understand dataset quality requirements
- Experience the full ML pipeline

**Note**: Can be done anytime. System works with pre-trained model, custom training is optional enhancement.

See [docs/YOLO_TRAINING.md](YOLO_TRAINING.md) for complete training guide.

---

### Component 4: Metadata Storage & API

**Goal**: Persistent storage and REST API

**Deliverables**:

- SQLite database with tables for:
  - `detections`: timestamp, image_path, detection_count
  - `detected_objects`: detection_id, class_name, confidence, bbox_coordinates
- FastAPI endpoints:
  - `GET /api/detections` - List recent detections
  - `GET /api/detections/{id}` - Single detection with image
  - `GET /api/timeline` - Aggregated timeline data
  - `GET /api/stats` - Summary statistics
- API documentation auto-generated at `/docs`

**Testing**: Use curl/Postman to test API endpoints

**Duration**: ~2-3 hours to implement and test

---

### Component 5: Web Interface - Basic View

**Goal**: Display detections in a simple web UI

**Deliverables**:

- React app with Mantine UI setup
- Homepage showing recent detections in a grid
- Each detection shows: thumbnail, timestamp, detected animals
- Click to view full-size image with bounding boxes
- Responsive design

**Testing**: Browse interface, verify images display correctly

**Duration**: ~3-4 hours to implement and test

---

### Component 6: Live Camera View & Real-Time Detection 🎥

**Goal**: See the camera feed live with detection visualization

**Deliverables**:

- **Live Camera Feed**: WebSocket-based MJPEG stream from camera to browser
- **Real-time Detection Overlay**: Bounding boxes drawn on live feed as detections happen
- **Visual Feedback**: Flash/highlight when photo is captured
- **Detection Labels**: Show detected object names and confidence scores on overlay
- **Performance Stats**: Display FPS, detection count, processing time
- **Toggle Controls**: Show/hide bounding boxes, adjust detection confidence threshold

**How It Works**:

- Backend streams camera frames via WebSocket at ~5-10 FPS
- Each frame is processed through YOLO
- Detection results (bounding boxes, labels) sent to frontend
- Frontend draws boxes using HTML5 Canvas over video feed
- Lower FPS than capture (live view doesn't need every frame)

**Testing**: Open live view in browser, move objects in front of camera, verify detections appear in real-time

**Duration**: ~3-4 hours to implement and test

---

### Component 7: Timeline Visualization

**Goal**: Interactive timeline showing animal activity

**Deliverables**:

- Timeline chart showing animal presence over time
- Filter by animal type
- Time range selector (last hour, 6 hours, 24 hours)
- "Session detection" - group consecutive detections of same animal
- Duration calculation (how long animal was present)
- Color-coded by animal type

**Testing**: Generate test data, verify timeline accuracy

**Duration**: ~4-5 hours to implement and test

---

### Component 8: Polish & Optimization

**Goal**: Production-ready system

**Deliverables**:

- Systemd service for auto-start on boot
- Configuration file for camera settings, detection thresholds
- Logging to file with rotation
- Performance optimization (reduce CPU usage between captures)
- Error handling and recovery
- Dark/light mode toggle
- Export data as CSV
- README with setup instructions

**Testing**: Full system test, simulate failures, measure resource usage

**Duration**: ~3-4 hours to implement and test

---

## Installation Prerequisites

```bash
# System packages (Raspberry Pi OS)
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv libcamera-dev python3-opencv

# Python environment
python3 -m venv venv
source venv/bin/activate

# Python packages (install as needed)
pip install picamera2 opencv-python ultralytics fastapi uvicorn sqlalchemy

# Node.js (for frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

## Database Schema

```sql
CREATE TABLE detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    image_path TEXT NOT NULL,
    detection_count INTEGER DEFAULT 0,
    processed BOOLEAN DEFAULT FALSE
);

CREATE TABLE detected_objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detection_id INTEGER NOT NULL,
    class_name TEXT NOT NULL,
    confidence REAL NOT NULL,
    bbox_x REAL NOT NULL,
    bbox_y REAL NOT NULL,
    bbox_width REAL NOT NULL,
    bbox_height REAL NOT NULL,
    FOREIGN KEY (detection_id) REFERENCES detections (id)
);

CREATE INDEX idx_detections_timestamp ON detections(timestamp);
CREATE INDEX idx_detected_objects_class ON detected_objects(class_name);
```

## Performance Considerations

- **Target**: Process 1 frame per second on Raspberry Pi 4
- **CPU Usage**: ~40-60% during active detection
- **Storage**: ~50MB per hour (720p images with 15min retention)
- **RAM**: ~500MB for Python process + model
- **Model Size**: YOLOv8n is ~6MB (compared to 90MB+ for larger variants)

## Future Enhancements (Post-MVP)

- Motion detection to trigger captures (save CPU when yard is empty)
- Email/push notifications for specific animals
- Night vision support (IR camera)
- Species-specific identification (fine-tuned model)
- Historical data retention (compressed/summarized)
- Multi-camera support
- Sound detection integration
- Picture-in-picture mode for live view
- Recording/replay of detection events

## Project Structure (Final)

```
pi-yard-tracker/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── camera.py            # Camera capture logic
│   ├── detector.py          # YOLO detection
│   ├── database.py          # SQLite models
│   ├── cleanup.py           # Photo deletion service
│   └── config.py            # Configuration
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom hooks
│   │   └── api/             # API client
│   └── package.json
├── data/
│   ├── photos/              # Captured images
│   └── tracker.db           # SQLite database
├── models/                  # YOLO model files
├── docs/                    # Documentation
└── README.md
```

---

## Getting Started 🚀

We'll build incrementally so you can test each component thoroughly. Start with camera capture and file management - no AI yet. This lets us verify hardware works before adding complexity.
