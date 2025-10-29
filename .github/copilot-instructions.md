# GitHub Copilot Instructions for Pi Yard Tracker

## Project Overview

**Pi Yard Tracker** is a Raspberry Pi-based wildlife detection system that uses computer vision to identify and track animals in a backyard setting. The project runs locally on a Raspberry Pi 5 with an OV5647 camera module, performing real-time object detection using YOLO models.

### Key Features
- **Local Processing**: All AI inference runs on-device, no cloud dependency
- **Custom Training**: Supports training custom YOLO models for specific animals (e.g., deer)
- **Synthetic Data Generation**: Uses OpenAI DALL-E 3 to generate training images when real photos aren't available
- **Automated Workflow**: Python scripts handle the complete pipeline from data generation to model testing

### Hardware Requirements
- Raspberry Pi 5 Model B (8GB recommended for inference, training requires external machine)
- OV5647 Camera Module (picamera2 compatible)
- MicroSD card (32GB+)
- Raspberry Pi OS (64-bit)

## Project Structure

```
pi-yard-tracker/
├── backend/                 # Python backend (organized by function)
│   ├── capture/             # Camera image capture (Pi only)
│   │   └── camera_capture.py
│   ├── detection/           # YOLO object detection
│   │   └── detector.py
│   └── training/            # Custom model training (GPU required)
│       ├── generate_training_data.py  # Synthetic data generation (DALL-E 3)
│       ├── prepare_dataset.py         # Dataset organization
│       ├── train_custom_model.py      # Model training script
│       ├── test_custom_model.py       # Model testing
│       ├── visualize_annotations.py   # Annotation verification
│       ├── cleanup_dataset.py         # Dataset cleanup
│       └── workflow.py                # End-to-end orchestration
├── data/                    # Dataset storage (gitignored)
│   ├── synthetic_training/  # Generated images + YOLO annotations
│   ├── training_data/       # Organized train/val/test splits
│   │   ├── images/
│   │   │   ├── train/
│   │   │   ├── val/
│   │   │   └── test/
│   │   └── labels/          # YOLO format annotations (.txt)
│   │       ├── train/
│   │       ├── val/
│   │       └── test/
│   ├── photos/              # Real captured photos
│   └── deer_dataset.yaml    # YOLO dataset configuration
├── models/                  # Model storage
│   ├── yolov8n.pt          # Pre-trained YOLOv8 Nano (80 COCO classes) - COMMITTED
│   └── custom_model/        # Custom trained model directory
│       └── weights/
│           ├── best.pt      # Best performing model - MUST BE COMMITTED
│           └── last.pt      # Latest training checkpoint - optional
├── docs/                    # Documentation
├── scripts/                 # Shell scripts for setup
└── .env                     # Environment variables (gitignored)
```

## Model Setup and Expectations

### Pre-trained Model (YOLOv8n)
- **Location**: `models/yolov8n.pt`
- **Status**: ✅ COMMITTED to git (6.3 MB)
- **Purpose**: Base model for detection and transfer learning
- **Classes**: 80 COCO classes (person, car, dog, cat, bird, etc.)
- **Usage**: Default detection, auto-annotation, transfer learning base
- **Download**: Automatically downloaded by ultralytics if missing, but we commit it for offline use

### Custom Model (Custom Deer Detector)
- **Location**: `models/custom_model/weights/best.pt`
- **Status**: ⚠️ MUST BE COMMITTED when trained
- **Purpose**: Production model for specific animal detection (e.g., deer)
- **Classes**: Defined in `data/deer_dataset.yaml` (typically 1 class: deer)
- **Training**: Must be done on a more powerful machine (not Raspberry Pi)
- **Size**: ~6-10 MB (similar to base model)

### .gitignore Configuration
```gitignore
# Keep base model
!models/yolov8n.pt

# Keep custom trained model
!models/custom_model/weights/best.pt

# Ignore training artifacts
models/custom_model/weights/last.pt
models/custom_model/weights/epoch*.pt
models/custom_model/*.csv
models/custom_model/*.yaml

# Ignore all other .pt files
*.pt
```

### Model Training Workflow (External Machine)

**The Raspberry Pi CANNOT train models** - it will run out of memory. Training must be done on a machine with:
- GPU (NVIDIA recommended, 8GB+ VRAM)
- 16GB+ RAM
- Ubuntu/Linux or Windows with WSL2

**Training Steps:**
1. Clone this repo on powerful machine
2. Generate synthetic training data: `python backend/generate_training_data.py --count 100`
3. Prepare dataset: `python backend/training/prepare_dataset.py`
4. Train model: `python backend/training/train_custom_model.py --epochs 100`
5. Copy `models/custom_model/weights/best.pt` back to Pi
6. **Commit `best.pt` to git** so others can use it

## Backend Scripts Reference

### capture/camera_capture.py
**Purpose**: Camera control and continuous image capture

**Key Functions:**
- `capture_images()`: Main loop capturing at 1 FPS
- `cleanup_old_captures()`: Auto-delete images older than 24 hours
- Uses picamera2 (must be installed system-wide on Pi)

**Usage:**
```bash
python backend/capture/camera_capture.py --interval 1.0 --output data/photos
```

**Dependencies**: picamera2 (system), pillow

---

### detection/detector.py
**Purpose**: YOLO object detection on images

**Key Classes:**
- `YOLODetector`: Wraps ultralytics YOLO model
  - `detect_objects()`: Run inference on image
  - `filter_animals()`: Filter for animal classes only
  - `save_detections()`: Save images with bounding boxes

**Usage:**
```bash
python backend/detection/detector.py --model models/yolov8n.pt --source data/photos/
```

**Model Support**: Both pre-trained (yolov8n.pt) and custom models

**Dependencies**: ultralytics, opencv-python, pillow

---

### training/generate_training_data.py
**Purpose**: Generate synthetic training images using OpenAI DALL-E 3

**Key Classes:**
- `SyntheticDataGenerator`: Handles image generation and annotation
  - `generate_image()`: Create image via DALL-E 3
  - `_edit_image_with_object()`: Scene-matching generation (GPT-4o Vision + DALL-E 3)
  - `auto_detect_bbox()`: Auto-annotate using pre-trained YOLO
  - `generate_training_sample()`: Complete image + annotation generation

**Two Modes:**
1. **From Scratch**: Generate based on text description
   ```bash
   python backend/training/generate_training_data.py \
       --object "white-tailed deer" \
       --background "outdoor backyard with grass and trees" \
       --count 100
   ```

2. **Scene Matching**: Generate based on existing photo
   ```bash
   python backend/training/generate_training_data.py \
       --object "white-tailed deer" \
       --base-image photos/backyard.jpg \
       --count 100
   ```

**Auto-Annotation**: Uses pre-trained YOLOv8n to detect actual object positions (not assumed centered)

**Output**: YOLO format annotations (.txt files)
```
0 0.49 0.56 0.29 0.60
# class_id x_center y_center width height (all normalized 0-1)
```

**Dependencies**: openai, pillow, requests, python-dotenv, ultralytics

**Environment**: Requires `OPENAI_API_KEY` in `.env`

**Cost**: ~$0.04 per image (DALL-E 3 standard quality)

---

### prepare_dataset.py
**Purpose**: Organize synthetic data into YOLO train/val/test structure

**Key Classes:**
- `DatasetPreparer`: Dataset organization and splitting
  - `create_directory_structure()`: Create YOLO folders
  - `find_image_label_pairs()`: Validate image-annotation pairs
  - `split_dataset()`: Random shuffle and split
  - `copy_files()`: Copy to train/val/test directories

**Usage:**
```bash
python backend/training/prepare_dataset.py \
    --input data/synthetic_training \
    --output data/training_data \
    --split 70 20 10 \
    --clean
```

**Default Split**: 70% train, 20% validation, 10% test

**Features**: Reproducible splits (--seed), validates pairs, logging

**Dependencies**: Python standard library only

---

### train_custom_model.py
**Purpose**: Train custom YOLO model using transfer learning

**Key Functions:**
- `validate_dataset()`: Check dataset structure and paths
- `train_model()`: Execute training with ultralytics

**Training Configuration:**
- **Transfer Learning**: Starts from YOLOv8n pre-trained weights
- **Optimizer**: Adam
- **Augmentation**: Automatic (mosaic, mixup, HSV)
- **Early Stopping**: Monitors validation loss

**Usage:**
```bash
python backend/training/train_custom_model.py \
    --dataset data/deer_dataset.yaml \
    --epochs 100 \
    --batch 16 \
    --model n
```

**Model Sizes**: n (nano), s (small), m (medium), l (large), x (extra-large)

**Output**: `models/custom_model/weights/best.pt`

**⚠️ WARNING**: Requires powerful machine, NOT Raspberry Pi!

**Dependencies**: ultralytics, pyyaml

---

### test_custom_model.py
**Purpose**: Test trained model on validation images

**Key Functions:**
- `test_model()`: Run inference on image directory
- Calculates detection statistics (total detections, confidence scores)

**Usage:**
```bash
python backend/training/test_custom_model.py \
    --model models/custom_model/weights/best.pt \
    --images data/training_data/images/val \
    --conf 0.25 \
    --save-results
```

**Output**: Annotated images with bounding boxes, detection statistics

**Dependencies**: ultralytics

---

### visualize_annotations.py
**Purpose**: Draw bounding boxes on images to verify annotations

**Key Classes:**
- `AnnotationVisualizer`: Annotation visualization
  - `parse_yolo_annotation()`: Read YOLO .txt files
  - `draw_box()`: Draw bounding box with label
  - `visualize_image()`: Process single image
  - `visualize_dataset()`: Process entire directory

**Usage:**
```bash
python backend/training/visualize_annotations.py \
    --input data/synthetic_training \
    --output data/annotation_check
```

**Output**: Images with green bounding boxes overlaid

**Use Case**: Verify auto-annotations are correct before training

**Dependencies**: pillow

---

### cleanup_dataset.py
**Purpose**: Remove training data and models to start fresh

**Key Classes:**
- `DatasetCleaner`: Dataset cleanup operations
  - `clean_synthetic_training()`: Remove generated images
  - `clean_prepared_dataset()`: Remove train/val/test splits
  - `clean_trained_models()`: Remove custom models
  - `clean_all()`: Remove everything

**Usage:**
```bash
# Remove everything
python backend/training/cleanup_dataset.py --all

# Selective cleanup
python backend/training/cleanup_dataset.py --synthetic-only
python backend/training/cleanup_dataset.py --prepared-only
python backend/training/cleanup_dataset.py --models-only
```

**Safety**: Logs file counts before deletion

**Dependencies**: Python standard library only

---

### workflow.py
**Purpose**: Orchestrate complete training pipeline

**Key Classes:**
- `TrainingWorkflow`: End-to-end pipeline orchestration
  - `step_generate_data()`: Generate synthetic images
  - `step_prepare_dataset()`: Organize dataset
  - `step_visualize_annotations()`: Verify annotations
  - `step_train_model()`: Train custom model
  - `step_test_model()`: Test trained model

**Usage:**
```bash
# Full workflow
python backend/training/workflow.py \
    --base-image photos/backyard.jpg \
    --count 100 \
    --epochs 100

# Skip specific steps
python backend/training/workflow.py \
    --skip-generation \
    --skip-preparation \
    --epochs 100
```

**Features**: 
- Step-by-step logging
- Time tracking per step
- Skip/resume capabilities
- Continue on error option

**Dependencies**: subprocess (calls other scripts)

---

## Python Coding Best Practices for This Project

### 1. Virtual Environment
```bash
# Create venv with system-site-packages (for picamera2 access)
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Imports Organization
```python
# Standard library
import argparse
import logging
from pathlib import Path

# Third-party
from ultralytics import YOLO
import cv2
from PIL import Image

# Local
from backend.detector import YOLODetector
```

### 3. Logging (Always Use)
```python
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("✅ Success message")
logger.warning("⚠️  Warning message")
logger.error("❌ Error message")
```

### 4. Path Handling (Use pathlib)
```python
from pathlib import Path

# Good
output_dir = Path('data/synthetic_training')
output_dir.mkdir(parents=True, exist_ok=True)
image_path = output_dir / f"image_{i}.jpg"

# Avoid
output_dir = 'data/synthetic_training'
os.makedirs(output_dir)  # Fails if exists
image_path = output_dir + '/image_' + str(i) + '.jpg'
```

### 5. Error Handling
```python
try:
    model = YOLO('models/yolov8n.pt')
except Exception as e:
    logger.error(f"❌ Failed to load model: {e}")
    return None
```

### 6. Type Hints
```python
from pathlib import Path
from typing import Optional, Tuple, List

def detect_objects(self, image_path: Path, confidence: float = 0.5) -> List[dict]:
    """
    Detect objects in image
    
    Args:
        image_path: Path to input image
        confidence: Minimum confidence threshold
        
    Returns:
        List of detection dictionaries
    """
    pass
```

### 7. CLI Arguments (argparse)
```python
parser = argparse.ArgumentParser(
    description='Script description',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  python script.py --input data/ --output results/
    """
)
parser.add_argument('--input', type=str, required=True, help='Input directory')
parser.add_argument('--output', type=str, default='output/', help='Output directory')
args = parser.parse_args()
```

### 8. Class Structure
```python
class YOLODetector:
    """Handles YOLO object detection"""
    
    def __init__(self, model_path: Path):
        """Initialize detector with model"""
        self.model_path = Path(model_path)
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Private method for model loading"""
        pass
    
    def detect_objects(self, image_path: Path) -> List[dict]:
        """Public method for detection"""
        pass
```

### 9. Constants at Module Level
```python
# At top of file after imports
DEFAULT_CONFIDENCE = 0.25
ANIMAL_CLASSES = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
OUTPUT_DIR = Path('data/detections')
```

### 10. Main Guard
```python
def main():
    """Main function"""
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    
    # Main logic here
    
if __name__ == "__main__":
    main()
```

## YOLO Format Reference

### Annotation Format (.txt files)
```
class_id x_center y_center width height
0 0.49 0.56 0.29 0.60
```
- All coordinates normalized 0-1 (relative to image dimensions)
- One line per object
- Same filename as image (e.g., `image.jpg` → `image.txt`)

### Dataset Configuration (deer_dataset.yaml)
```yaml
path: /absolute/path/to/data/training_data
train: images/train
val: images/val
test: images/test  # optional

nc: 1              # number of classes
names:
  0: deer          # class mapping
```

## Common Issues and Solutions

### Issue: picamera2 not found
**Solution**: Install system-wide, create venv with `--system-site-packages`

### Issue: Training kills Raspberry Pi
**Solution**: Train on powerful machine, copy `best.pt` back to Pi

### Issue: No animals detected in generated images
**Solution**: DALL-E 3 sometimes generates abstract images. Verify with `visualize_annotations.py`, regenerate if needed.

### Issue: OpenAI API errors
**Solution**: Check `.env` has valid `OPENAI_API_KEY`, check billing/limits

### Issue: Model not found
**Solution**: Ensure `models/custom_model/weights/best.pt` exists and is committed to git

## Development Workflow

1. **Capture real photos**: `python backend/capture/camera_capture.py`
2. **Generate synthetic data**: `python backend/generate_training_data.py`
3. **Verify annotations**: `python backend/training/visualize_annotations.py`
4. **Prepare dataset**: `python backend/training/prepare_dataset.py`
5. **Train on powerful machine**: `python backend/training/train_custom_model.py`
6. **Test model**: `python backend/training/test_custom_model.py`
7. **Commit `best.pt`**: `git add models/custom_model/weights/best.pt && git commit`
8. **Deploy to Pi**: Pull repo, run `backend/detector.py` with custom model

## Future Phases

- **Phase 3**: Database (SQLite) + REST API (FastAPI)
- **Phase 4**: Web UI for viewing detections
- **Phase 4.5**: Live camera view
- **Phase 5**: Timeline visualization

## Environment Variables

Required in `.env`:
```bash
# Optional: Only needed for synthetic data generation
OPENAI_API_KEY=sk-...
```

## When Suggesting Code

1. **Always use logging** instead of print statements
2. **Use pathlib.Path** for all file operations
3. **Include type hints** for function signatures
4. **Add docstrings** to all functions and classes
5. **Handle errors gracefully** with try/except and logging
6. **Use argparse** for CLI scripts
7. **Follow existing code style** (see backend/*.py for examples)
8. **Test on actual Raspberry Pi** when possible (especially camera/picamera2 code)
9. **Remember**: Training happens on powerful machine, inference on Pi
10. **Commit trained models**: `best.pt` must be in git for deployment

## Model Deployment Checklist

Before committing:
- [ ] Model trained with 100+ images
- [ ] Validation accuracy >70%
- [ ] Tested on real backyard photos
- [ ] File size <20MB
- [ ] Located at `models/custom_model/weights/best.pt`
- [ ] Updated documentation with model performance metrics
- [ ] `.gitignore` configured to keep `best.pt`
