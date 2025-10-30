# Pi Yard Tracker - File Guide

**Last Updated**: 2025-01-28

This guide explains what each Python file does and whether it should be run directly or imported.

## ⚠️ CRITICAL: Entry Point

**ONLY ONE WAY TO START THE SYSTEM:**

```bash
python run_camera_system.py
```

This single command starts:

- SharedCameraManager (camera with dual outputs)
- CameraCapture thread (saves 1920x1080 photos every 10 seconds)
- YOLODetector (runs detection on every photo)
- Database integration (saves photos + detections to SQLite)
- LiveCameraManager (provides 640x480 stream for WebSocket)
- FastAPI server (REST API + WebSocket /live endpoint on port 8000)
- PhotoCleanupService (deletes old photos automatically)

**DO NOT:**

- Run `uvicorn backend.api.main:app` directly
- Run any backend/capture/\*.py files directly
- Create startup scripts for individual components

**Why?** All components share the same camera resource and must be coordinated in a single process.

---

## Root Level Files

### run_camera_system.py

- **Purpose**: Main entry point for complete system
- **Run directly**: ✅ YES - This is the only file you should run
- **What it does**:
  - Starts SharedCameraManager
  - Starts PhotoCleanupService in background thread
  - Starts CameraCapture thread (if --no-capture not set)
  - Initializes YOLODetector
  - Starts LiveCameraManager (if --capture-only not set)
  - Runs FastAPI server with uvicorn
- **Arguments**:
  - `--interval`: Capture interval in seconds (default: 10.0)
  - `--port`: API port (default: 8000)
  - `--model`: YOLO model path (default: models/custom_model/weights/best.pt)
  - `--confidence`: Detection confidence threshold (default: 0.25)
  - `--retention-hours`: Photo retention in hours (default: 1)
  - `--cleanup-interval`: Cleanup check interval in seconds (default: 300)
  - `--no-capture`: Live stream only mode
  - `--capture-only`: No live stream mode
- **Dependencies**: picamera2 (system), ultralytics, fastapi, uvicorn

---

## backend/

### backend/shared_camera.py

- **Purpose**: Singleton camera manager with dual outputs
- **Run directly**: ❌ NO - Imported by run_camera_system.py
- **What it does**:
  - Provides `SharedCameraManager` class
  - Main output: 1920x1080 @ 1 FPS (for photo capture)
  - Lores output: 640x480 @ 15 FPS (for live stream)
  - Ensures only one camera instance exists
- **Key methods**:
  - `get_main_frame()`: Get high-res frame for photo capture
  - `get_lores_frame()`: Get low-res frame for live streaming
  - `stop()`: Stop camera and cleanup

### backend/cleanup_service.py

- **Purpose**: Automatic photo file cleanup
- **Run directly**: ❌ NO - Now integrated into run_camera_system.py
- **What it does**:
  - Provides `PhotoCleanupService` class
  - Deletes photo files older than retention period
  - Preserves database records (only deletes files)
  - Runs in background thread with signal handlers
- **Default behavior**:
  - Retention: 1 hour
  - Check interval: 5 minutes (300 seconds)
- **Note**: Previously could be run standalone, now integrated into main system

---

## backend/api/

### backend/api/main.py

- **Purpose**: FastAPI application definition
- **Run directly**: ❌ NO - Imported by run_camera_system.py
- **What it does**:
  - Defines `app = FastAPI(...)`
  - Registers route blueprints (photos, detections, stats)
  - Defines WebSocket endpoint `/live`
  - CORS middleware configuration
- **Endpoints**:
  - `GET /`: Health check
  - `GET /photos`: List photos with optional detection filter
  - `GET /photos/{photo_id}`: Get single photo with detections
  - `GET /detections`: List all detections
  - `GET /stats`: Detection statistics
  - `WebSocket /live`: Live camera feed with detection overlays
- **Note**: This is JUST the app definition. Running uvicorn directly will start API without camera/database.

### backend/api/live_stream.py

- **Purpose**: LiveCameraManager for WebSocket streaming
- **Run directly**: ❌ NO - Imported by run_camera_system.py
- **What it does**:
  - Provides `LiveCameraManager` class
  - Reads frames from SharedCameraManager lores output
  - Runs YOLO detection on every frame (640x480 @ 15 FPS)
  - Draws bounding boxes on frames
  - Encodes frames as JPEG
  - Sends to WebSocket clients
  - Sends detection metadata as JSON
- **Key methods**:
  - `get_stream()`: Async generator for frames
  - `handle_websocket()`: WebSocket connection handler
- **Default model**: models/custom_model/weights/best.pt

### backend/api/schemas.py

- **Purpose**: Pydantic models for API responses
- **Run directly**: ❌ NO - Imported by routes
- **What it does**:
  - Defines response schemas (PhotoResponse, DetectionResponse, StatsResponse)
  - Used for automatic API documentation and validation

---

## backend/api/routes/

### backend/api/routes/photos.py

- **Purpose**: Photo-related API endpoints
- **Run directly**: ❌ NO - Imported by main.py
- **Endpoints**:
  - `GET /photos`: List photos with optional filters
  - `GET /photos/{photo_id}`: Get single photo details

### backend/api/routes/detections.py

- **Purpose**: Detection-related API endpoints
- **Run directly**: ❌ NO - Imported by main.py
- **Endpoints**:
  - `GET /detections`: List all detections with optional filters

### backend/api/routes/stats.py

- **Purpose**: Statistics API endpoint
- **Run directly**: ❌ NO - Imported by main.py
- **Endpoints**:
  - `GET /stats`: Detection statistics (total photos, detections, classes, etc.)

---

## backend/database/

### backend/database/db.py

- **Purpose**: Database connection and initialization
- **Run directly**: ❌ NO - Imported by queries.py
- **What it does**:
  - Provides `get_db()` function for database connections
  - Initializes database from schema.sql if needed
  - Thread-safe connection management

### backend/database/models.py

- **Purpose**: SQLAlchemy ORM models
- **Run directly**: ❌ NO - Imported by queries.py
- **Models**:
  - `Photo`: photo metadata (filename, dimensions, timestamps)
  - `Detection`: object detection results (class, confidence, bbox)
  - `Session`: capture session tracking

### backend/database/queries.py

- **Purpose**: Database query functions
- **Run directly**: ❌ NO - Imported by run_camera_system.py and API routes
- **Functions**:
  - `create_photo()`: Insert photo record
  - `create_detection()`: Insert detection record
  - `create_session()`: Start capture session
  - `get_photos()`: Query photos with filters
  - `get_detections()`: Query detections
  - `get_stats()`: Get detection statistics

### backend/database/schema.sql

- **Purpose**: SQLite database schema
- **Run directly**: ❌ NO - Executed by db.py on initialization
- **Tables**: photos, detections, sessions

---

## backend/detection/

### backend/detection/detector.py

- **Purpose**: YOLO object detection wrapper
- **Run directly**: ❌ NO - Imported by run_camera_system.py and live_stream.py
- **What it does**:
  - Provides `YOLODetector` class
  - Wraps ultralytics YOLO model
  - Runs inference on images
  - Draws bounding boxes on images
  - Saves annotated images to data/photos/detections/
- **Key methods**:
  - `detect()`: Run detection on image
  - `save_visualization()`: Save image with bounding boxes

---

## backend/training/

**All training scripts run OUTSIDE the main system. Training should be done on a powerful machine, not the Raspberry Pi.**

### backend/training/generate_training_data.py

- **Purpose**: Generate synthetic training images using DALL-E 3
- **Run directly**: ✅ YES - For dataset creation
- **Usage**:
  ```bash
  python backend/training/generate_training_data.py \
      --object "white-tailed deer" \
      --background "outdoor backyard" \
      --count 100
  ```
- **Output**: Images + YOLO annotations in data/synthetic_training/

### backend/training/prepare_dataset.py

- **Purpose**: Organize images into YOLO train/val/test structure
- **Run directly**: ✅ YES - After generating data
- **Usage**:
  ```bash
  python backend/training/prepare_dataset.py \
      --input data/synthetic_training \
      --output data/training_data \
      --split 70 20 10
  ```
- **Output**: Organized dataset in data/training_data/

### backend/training/train_custom_model.py

- **Purpose**: Train custom YOLO model using transfer learning
- **Run directly**: ✅ YES - On powerful machine (NOT Raspberry Pi)
- **Usage**:
  ```bash
  python backend/training/train_custom_model.py \
      --dataset data/deer_dataset.yaml \
      --epochs 100 \
      --batch 16
  ```
- **Output**: Trained model at models/custom_model/weights/best.pt
- **⚠️ WARNING**: Requires GPU, 16GB+ RAM

### backend/training/test_custom_model.py

- **Purpose**: Test trained model on validation images
- **Run directly**: ✅ YES - After training
- **Usage**:
  ```bash
  python backend/training/test_custom_model.py \
      --model models/custom_model/weights/best.pt \
      --images data/training_data/images/val
  ```

### backend/training/visualize_annotations.py

- **Purpose**: Draw bounding boxes to verify annotations
- **Run directly**: ✅ YES - For dataset verification
- **Usage**:
  ```bash
  python backend/training/visualize_annotations.py \
      --input data/synthetic_training \
      --output data/annotation_check
  ```

### backend/training/auto_annotate.py

- **Purpose**: Auto-annotate images using pre-trained YOLO
- **Run directly**: ✅ YES - For creating training data from photos
- **Usage**:
  ```bash
  python backend/training/auto_annotate.py \
      --input data/photos \
      --output data/synthetic_training \
      --classes 0 15 16 17
  ```

### backend/training/cleanup_dataset.py

- **Purpose**: Remove training data to start fresh
- **Run directly**: ✅ YES - For cleanup
- **Usage**:
  ```bash
  python backend/training/cleanup_dataset.py --all
  ```

### backend/training/workflow.py

- **Purpose**: Orchestrate complete training pipeline
- **Run directly**: ✅ YES - For end-to-end training
- **Usage**:
  ```bash
  python backend/training/workflow.py \
      --base-image photos/backyard.jpg \
      --count 100 \
      --epochs 100
  ```

### Other training files

- `annotation_tool.py`: Manual annotation GUI
- `convert_annotations.py`: Convert between annotation formats
- `fetch_images.py`: Download images from web
- `verify_setup.py`: Verify training environment

---

## Deleted Legacy Files

These files/folders were removed during cleanup (2025-10-30):

- ❌ `backend/capture/` (entire folder): Standalone capture scripts replaced by run_camera_system.py integration
  - `camera_capture.py`: Standalone capture script
  - `shared_camera_integration.py`: Example code, not used in production
  - `README.md`: Outdated documentation
  - `__init__.py`: Empty module file

---

## Port Configuration

| Port     | Service                                     | Status           |
| -------- | ------------------------------------------- | ---------------- |
| **8000** | Complete backend (camera + API + WebSocket) | ✅ **DEFAULT**   |
| 5173     | Frontend dev server (Vite)                  | Development only |

**IMPORTANT**: Port 8000 is the standard and should NEVER be changed unless there's a conflict.

---

## Common Mistakes

### ❌ DO NOT DO THIS:

```bash
# WRONG - Starts API without camera system
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# WRONG - Legacy standalone capture
python backend/capture/camera_capture.py

# WRONG - Standalone cleanup (now integrated)
python backend/cleanup_service.py
```

### ✅ DO THIS INSTEAD:

```bash
# CORRECT - Single entry point for everything
python run_camera_system.py
```

---

## Development Workflow

1. **Daily Use**: `python run_camera_system.py`
2. **Custom Training**: Use backend/training/\*.py scripts on powerful machine
3. **Testing**: Access API docs at http://localhost:8000/docs
4. **Frontend**: Run Vite dev server separately (port 5173)

---

## Questions?

- **Q: How do I start the camera?**  
  A: `python run_camera_system.py`

- **Q: How do I change the capture interval?**  
  A: `python run_camera_system.py --interval 5.0`

- **Q: How do I train a custom model?**  
  A: Use backend/training/workflow.py on a powerful machine

- **Q: How do I change photo retention?**  
  A: `python run_camera_system.py --retention-hours 24`

- **Q: Can I run the API separately?**  
  A: No. It must run as part of run_camera_system.py to access camera and database.

- **Q: What if I see "camera already in use" error?**  
  A: Only one instance of run_camera_system.py can run at a time. Kill any existing processes.
