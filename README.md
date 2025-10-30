# Pi Yard Tracker

Wildlife monitoring system for Raspberry Pi with local AI detection and web visualization.

## 🎉 What We've Built

**The complete system is ready!** The system can now:

- 📷 Capture photos from Raspberry Pi camera every second
- 💾 Store full HD images (1920x1080) locally
- 🤖 Detect objects using YOLOv8n AI model (~300-400ms per photo)
- 🎯 Identify 80 object classes (person, dog, cat, bird, etc.) OR custom classes
- 🎨 Train custom models for specific objects (e.g., coffee mugs, specific animals)
- 🖼️ Save images with bounding boxes drawn around detected objects
- 🗑️ Automatically delete photos older than 15 minutes
- 📊 Log detection results in real-time
- 💾 Store photos and detections in SQLite database
- 🌐 REST API for querying photos, detections, and statistics
- 📈 Interactive API documentation (Swagger UI)

See [docs/YOLO_EXPLAINED.md](docs/YOLO_EXPLAINED.md) for technical details.

## Quick Start

### Complete System (Recommended)

This starts everything in one process: camera capture, detection, database, API, live streaming, and automatic cleanup.

```bash
# Initial setup (run once)
./setup.sh

# Start the complete system (captures photo every 10 seconds, auto-cleanup every 5 minutes)
source venv/bin/activate
python run_camera_system.py

# Or use the startup script
./start_system.sh
```

**What runs on startup:**

- 📷 Camera capture (saves 1920x1080 photos every 10 seconds)
- 🤖 YOLO detection (runs on every captured photo)
- 💾 Database (saves photos + detections to SQLite)
- 🌐 REST API (port 8000, access at http://localhost:8000/docs)
- 📡 Live WebSocket stream (640x480 feed for web UI)
- 🧹 Automatic cleanup (deletes photos older than 1 hour, preserves DB records)

### Custom Configuration

```bash
# Use custom model
python run_camera_system.py --model models/custom_model/weights/best.pt

# Change capture interval (default: 10 seconds)
python run_camera_system.py --interval 5.0

# Change photo retention (default: 1 hour)
python run_camera_system.py --retention-hours 24

# Change cleanup check interval (default: 300 seconds = 5 minutes)
python run_camera_system.py --cleanup-interval 600
```

# Adjust confidence threshold (default: 0.25)

python run_camera_system.py --confidence 0.5

# Live stream only (no photo capture)

python run_camera_system.py --no-capture

# Photo capture only (no live stream)

python run_camera_system.py --capture-only

````

### Legacy Mode (Separate Processes - NOT RECOMMENDED)

⚠️ **This method is deprecated. Use `run_camera_system.py` instead.**

<details>
<summary>Click to expand legacy instructions</summary>

```bash
# Start API server (Terminal 1) - API ONLY, no camera
source venv/bin/activate
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# Start cleanup service (Terminal 2)
source venv/bin/activate
python backend/cleanup_service.py --retention-hours 24

# Start camera capture (Terminal 3) - STANDALONE, doesn't integrate with API
source venv/bin/activate
python backend/capture/camera_capture.py
````

**Problems with this approach:**

- Camera and API run as separate processes
- Live streaming doesn't work (no camera feed to WebSocket)
- Harder to manage and debug
- Resource contention issues

</details>

### View Results

- **Photos**: Saved to `data/photos/`
- **Detections**: Saved to `data/photos/detections/` with bounding boxes
- **Database**: SQLite database at `data/detections.db` (retains all history)
- **Cleanup**: Old photo files automatically deleted (database records preserved)
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **API Health**: http://localhost:8000/health

### Cleanup Service Options

The cleanup service runs independently and manages disk space:

```bash
# Default: Delete files older than 24 hours, check every 5 minutes
python backend/cleanup_service.py

# Custom retention: keep files for 48 hours
python backend/cleanup_service.py --retention-hours 48

# Check more frequently: every 1 minute
python backend/cleanup_service.py --check-interval 60

# Show current storage statistics
python backend/cleanup_service.py --stats

# Run cleanup once and exit (useful for cron jobs)
python backend/cleanup_service.py --run-once
```

**Note**: The cleanup service only deletes photo **files** from disk. All database records (photos, detections, sessions) are **preserved** indefinitely. This allows you to query historical data via the API while managing disk space.

### Query the API

```bash
# Get overall statistics
curl http://localhost:8000/stats | python3 -m json.tool

# Get recent photos
curl http://localhost:8000/photos/?limit=10 | python3 -m json.tool

# Get photos with detections only
curl "http://localhost:8000/photos/?has_detections=true&limit=10" | python3 -m json.tool

# Get recent detections
curl http://localhost:8000/detections/?limit=10 | python3 -m json.tool

# Get specific class detections (e.g., coffee_mug)
curl "http://localhost:8000/detections/?class_name=coffee_mug&min_confidence=0.5" | python3 -m json.tool

# Get detection class breakdown
curl http://localhost:8000/detections/classes | python3 -m json.tool
```

## Models

The project uses YOLOv8 for object detection:

- **`models/yolov8n.pt`** (6.3 MB) - Pre-trained YOLOv8 Nano model
  - Included in repository for immediate use
  - Detects 80 COCO object classes
  - Used for both detection and transfer learning
  - Downloaded automatically if missing via Ultralytics

Custom trained models (e.g., `models/custom_model/`) are **not** committed to git.
Train your own custom models using the scripts in `backend/` - see [docs/PYTHON_WORKFLOW.md](docs/PYTHON_WORKFLOW.md).

## Training Custom Models

### Option 1: Generate Synthetic Training Data (OpenAI DALL-E 3)

```bash
# 1. Set up OpenAI API key in .env
OPENAI_API_KEY=sk-your-key-here

# 2. Generate synthetic training images (costs ~$0.04 per image)
python backend/training/generate_training_data.py \
    --object "coffee mug" \
    --background "kitchen countertop with natural lighting" \
    --count 100

# 3. Prepare dataset (organize into train/val/test splits)
python backend/training/prepare_dataset.py \
    --input data/synthetic_training \
    --output data/training_data \
    --split 70 20 10 \
    --clean

# 4. Train custom model
python backend/training/train_custom_model.py \
    --dataset data/coffee_mug_dataset.yaml \
    --epochs 100 \
    --batch 8 \
    --model n

# 5. Test the trained model
python backend/training/test_custom_model.py \
    --model models/custom_model/weights/best.pt \
    --images data/training_data/images/val \
    --confidence 0.25
```

### Option 2: Download Real Images from Pexels (FREE)

```bash
# 1. Set up Pexels API key in .env (FREE - no rate limits)
PEXELS_API_KEY=your-key-here

# 2. Fetch real stock photos from Pexels
python backend/training/fetch_images.py \
    --query "coffee mug" \
    --count 30 \
    --source pexels

# 3. Auto-annotate images using pre-trained YOLOv8n
python backend/training/auto_annotate.py \
    --input data/to_annotate \
    --output data/to_annotate \
    --model models/yolov8n.pt \
    --class-ids 0

# 4. Manually review and correct annotations in GUI
python backend/training/annotation_tool.py \
    --input data/to_annotate \
    --class-ids 0

# 5. Click "Add to Training Set" button in GUI when done annotating

# 6. Prepare dataset (organize into train/val/test splits)
python backend/training/prepare_dataset.py \
    --input data/synthetic_training \
    --output data/training_data \
    --split 70 20 10 \
    --clean

# 7. Train custom model
python backend/training/train_custom_model.py \
    --dataset data/coffee_mug_dataset.yaml \
    --epochs 100 \
    --batch 8 \
    --model n

# 8. Test the trained model
python backend/training/test_custom_model.py \
    --model models/custom_model/weights/best.pt \
    --images data/training_data/images/val \
    --confidence 0.25
```

**Pro Tips:**

- **Pexels method** is FREE
- **OpenAI method** is faster but costs ~$4 for 100 images
- You need **100-500+ images** for good model performance
- Mix both methods for best results (diverse training data)
- Use different search queries: "coffee mug", "white ceramic mug", "coffee cup on desk", etc.
- Lower confidence threshold (0.01-0.10) may be needed for custom models vs pre-trained (0.25)

## Configuration

Edit `.env` to adjust settings:

- `CAPTURE_INTERVAL`: Seconds between photos (default: 1)
- `RETENTION_MINUTES`: How long to keep photos (default: 15)
- `CLEANUP_INTERVAL`: How often to check for old files (default: 30)

Or edit `backend/camera_capture.py` directly:

- `DETECTION_ENABLED`: Enable/disable YOLO detection (default: True)
- `CONFIDENCE_THRESHOLD`: Minimum confidence for detections (default: 0.5)
- `SAVE_DETECTIONS`: Save images with bounding boxes (default: True)

## Documentation

- [📋 Complete Project Plan](docs/PROJECT_PLAN.md) - Full roadmap and technical stack
- [🎥 Live View Details](docs/LIVE_VIEW.md) - Real-time detection visualization

## Features

✅ **Camera Capture & Basic Storage**

- Camera initialization and configuration
- 1-second interval photo capture
- Automatic 15-minute retention cleanup
- Logging and statistics

✅ **Object Detection - Pre-trained Model**

- YOLOv8n integration (~6MB model)
- Real-time detection on every photo (~300-400ms)
- 80 object classes (person, animals, vehicles, etc.)
- Bounding box visualization
- Detection logging

✅ **Custom Model Training**

- Synthetic training data generation using AI (DALL-E 3)
- Real image fetching from Pexels (FREE)
- Automatic YOLO-format annotations
- Manual annotation GUI tool
- Transfer learning from YOLOv8n
- Custom model deployment
- See [docs/SYNTHETIC_DATA_GENERATION.md](docs/SYNTHETIC_DATA_GENERATION.md)

✅ **Database & REST API**

- SQLite database for photos and detections
- FastAPI REST API with Swagger UI
- Pagination, filtering, and statistics endpoints
- Session tracking
- See [backend/database/README.md](backend/database/README.md) and [backend/api/README.md](backend/api/README.md)

## Planned Features

- 🔜 Web Interface - Photo gallery and detection timeline
- 🔜 Live Camera View & Real-Time Detection 🎥
- 🔜 Timeline Visualization
- 🔜 Enhanced UI Polish & Optimization

## Hardware Used

- **Raspberry Pi 5 Model B** (also works on Pi 4)
- **OV5647 Camera Module** (5MP, detected automatically)
