# Pi Yard Tracker

Wildlife monitoring system for Raspberry Pi with local AI detection and web visualization.

## 🎉 What We've Built So Far

**Phase 1 & 2A are complete!** The system can now:
- 📷 Capture photos from Raspberry Pi camera every second
- 💾 Store full HD images (1920x1080) locally
- 🤖 Detect objects using YOLOv8n AI model (~420ms per photo)
- 🎯 Identify 80 object classes (person, dog, cat, bird, etc.)
- 🖼️ Save images with bounding boxes drawn around detected objects
- 🗑️ Automatically delete photos older than 15 minutes
- 📊 Log detection results in real-time

See [docs/PHASE_1_SUMMARY.md](docs/PHASE_1_SUMMARY.md) and [docs/YOLO_EXPLAINED.md](docs/YOLO_EXPLAINED.md) for details.

## Quick Start

```bash
# Initial setup (run once)
./setup.sh

# Run camera capture
source venv/bin/activate
python backend/camera_capture.py
```

Photos are saved to `data/photos/` and automatically deleted after 15 minutes.

## Models

The project uses YOLOv8 for object detection:

- **`models/yolov8n.pt`** (6.3 MB) - Pre-trained YOLOv8 Nano model
  - Included in repository for immediate use
  - Detects 80 COCO object classes
  - Used for both detection and transfer learning
  - Downloaded automatically if missing via Ultralytics

Custom trained models (e.g., `models/custom_model/`) are **not** committed to git.
Train your own custom models using the scripts in `backend/` - see [docs/PYTHON_WORKFLOW.md](docs/PYTHON_WORKFLOW.md).

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
- [✅ Phase 1 Summary](docs/PHASE_1_SUMMARY.md) - What we built and how it works
- [🎥 Live View Details](docs/LIVE_VIEW.md) - Real-time detection visualization (coming in Phase 4.5)

## Project Status

✅ **Phase 1: Camera Capture & Basic Storage** (COMPLETE)
- Camera initialization and configuration
- 1-second interval photo capture
- Automatic 15-minute retention cleanup
- Logging and statistics

✅ **Phase 2A: Object Detection - Pre-trained Model** (COMPLETE)
- YOLOv8n integration (~6MB model)
- Real-time detection on every photo (~420ms)
- 80 object classes (person, animals, vehicles, etc.)
- Bounding box visualization
- Detection logging

🔄 **Phase 2B: Synthetic Training Data Generation** (IN PROGRESS)
- Generate realistic training images using AI (DALL-E 3)
- Automatic YOLO-format annotations
- No need for 1000+ manual photos!
- See [docs/SYNTHETIC_DATA_GENERATION.md](docs/SYNTHETIC_DATA_GENERATION.md)

⬜ **Phase 3: Metadata Storage & API** (Next)
- SQLite database for detections
- FastAPI REST endpoints

⬜ **Phase 4: Web Interface - Basic View**
⬜ **Phase 4.5: Live Camera View & Real-Time Detection** 🎥
⬜ **Phase 5: Timeline Visualization**
⬜ **Phase 6: Polish & Optimization**

## Hardware Used

- **Raspberry Pi 5 Model B** (also works on Pi 4)
- **OV5647 Camera Module** (5MP, detected automatically)
