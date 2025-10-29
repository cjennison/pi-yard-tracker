# Backend

Python backend for Pi Yard Tracker, organized into modular components.

## Directory Structure

```
backend/
├── capture/              # Camera image capture
│   ├── camera_capture.py
│   └── README.md
├── detection/            # Object detection with YOLO
│   ├── detector.py
│   └── README.md
└── training/             # Custom model training (GPU required)
    ├── generate_training_data.py
    ├── prepare_dataset.py
    ├── train_custom_model.py
    ├── test_custom_model.py
    ├── visualize_annotations.py
    ├── cleanup_dataset.py
    ├── workflow.py
    └── README.md
```

## Module Overview

### 📷 Capture
**Location**: `backend/capture/`  
**Purpose**: Image capture from Raspberry Pi camera module  
**Runs on**: Raspberry Pi only  
**Key Script**: `camera_capture.py`

Handles continuous image capture at 1 FPS with automatic cleanup of old images.

### 🔍 Detection
**Location**: `backend/detection/`  
**Purpose**: YOLO object detection on images  
**Runs on**: Raspberry Pi or any machine  
**Key Script**: `detector.py`

Performs object detection using pre-trained or custom YOLO models. Can run on Pi for inference.

### 🎓 Training
**Location**: `backend/training/`  
**Purpose**: Custom model training pipeline  
**Runs on**: ⚠️ **GPU machine ONLY** (NOT Raspberry Pi)  
**Key Script**: `workflow.py` (orchestrates all steps)

Complete pipeline for:
1. Synthetic data generation (OpenAI DALL-E 3)
2. Dataset preparation (train/val/test splits)
3. Annotation visualization
4. Model training (transfer learning)
5. Model testing

## Quick Start

### On Raspberry Pi (Capture + Detection)

```bash
# 1. Capture images
python backend/capture/camera_capture.py --interval 1.0

# 2. Run detection with pre-trained model
python backend/detection/detector.py \
    --model models/yolov8n.pt \
    --source data/photos/

# 3. Or with custom model (after training)
python backend/detection/detector.py \
    --model models/custom_model/weights/best.pt \
    --source data/photos/
```

### On GPU Machine (Training)

```bash
# Complete training workflow
python backend/training/workflow.py \
    --base-image photos/backyard.jpg \
    --count 100 \
    --epochs 100

# Copy trained model back to Pi
scp models/custom_model/weights/best.pt pi@raspberrypi:~/pi-yard-tracker/models/custom_model/weights/
```

## Dependencies

See [requirements.txt](../requirements.txt) for all dependencies.

**System Requirements:**
- **Raspberry Pi**: picamera2 (system-wide)
- **GPU Machine**: NVIDIA GPU with 8GB+ VRAM (for training)

## Environment Variables

Create `.env` in project root:

```bash
# Optional: Only for synthetic data generation
OPENAI_API_KEY=sk-...
```

## Architecture Principles

1. **Separation of Concerns**: Each module handles one aspect (capture, detection, training)
2. **Platform Awareness**: Training scripts know they need GPU, capture scripts need Pi
3. **Reusable Components**: Classes can be imported and used programmatically
4. **CLI First**: All scripts have command-line interfaces
5. **Logging**: Comprehensive logging with emoji indicators

## Common Workflows

### Development Workflow (Full Pipeline)
1. **On Pi**: Capture real backyard photos
2. **On GPU machine**: Generate synthetic data, train model
3. **Transfer**: Copy `best.pt` back to Pi
4. **On Pi**: Run detection with custom model

### Testing Workflow
1. **On GPU machine**: Generate test data, train small model
2. **On GPU machine**: Test model accuracy
3. **Transfer**: Deploy to Pi if satisfactory

### Production Workflow
1. **On Pi**: Continuous capture at 1 FPS
2. **On Pi**: Detection runs on new images
3. **Future**: Database stores detections, API serves results

## See Also

- [.github/copilot-instructions.md](../.github/copilot-instructions.md) - Complete project documentation
- [docs/PYTHON_WORKFLOW.md](../docs/PYTHON_WORKFLOW.md) - Detailed training workflow
- [docs/YOLO_EXPLAINED.md](../docs/YOLO_EXPLAINED.md) - YOLO concepts explained
