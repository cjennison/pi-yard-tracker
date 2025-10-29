# Models Directory

This directory contains YOLO models used for wildlife detection.

## Files

### `yolov8n.pt` (Pre-trained Base Model)
- **Size**: 6.3 MB
- **Status**: ✅ Committed to git
- **Classes**: 80 COCO classes (person, car, dog, cat, bird, etc.)
- **Purpose**: 
  - Base detection for general objects
  - Transfer learning starting point
  - Auto-annotation of synthetic training data
- **Source**: Ultralytics YOLOv8 Nano
- **Performance on Pi 5**: ~420ms inference time

### `custom_model/weights/best.pt` (Custom Trained Model)
- **Size**: ~6-10 MB (when trained)
- **Status**: ⚠️ TO BE ADDED after training
- **Classes**: 1 class (deer) - defined in `data/deer_dataset.yaml`
- **Purpose**: Production model for specific wildlife detection
- **Training**: Must be done on powerful machine (GPU recommended)
- **Performance**: Expected 75-85% accuracy with 100+ training images

## Training Workflow

**⚠️ IMPORTANT**: The Raspberry Pi CANNOT train models due to memory limitations.

### On Powerful Machine (GPU recommended):

1. Clone this repository
2. Generate training data:
   ```bash
   python backend/generate_training_data.py --count 100 --background "outdoor backyard"
   ```
3. Prepare dataset:
   ```bash
   python backend/prepare_dataset.py --input data/synthetic_training --output data/training_data
   ```
4. Train model:
   ```bash
   python backend/train_custom_model.py --dataset data/deer_dataset.yaml --epochs 100
   ```
5. Copy `models/custom_model/weights/best.pt` to this directory
6. **Commit to git**: `git add models/custom_model/weights/best.pt && git commit -m "Add custom deer detection model"`

### On Raspberry Pi (Inference Only):

```bash
# Pull latest code with trained model
git pull

# Run detection
python backend/detector.py --model models/custom_model/weights/best.pt --source data/photos/
```

## Model Requirements

- **Training Machine**: 
  - GPU: NVIDIA with 8GB+ VRAM (recommended)
  - RAM: 16GB+
  - OS: Ubuntu/Linux or Windows with WSL2
  
- **Raspberry Pi** (Inference only):
  - Model: Pi 5 Model B
  - RAM: 8GB recommended
  - Inference time: ~400-500ms per image

## .gitignore Configuration

The `.gitignore` is configured to:
- ✅ Keep `yolov8n.pt` (base model)
- ✅ Keep `custom_model/weights/best.pt` (custom trained model)
- ❌ Ignore training artifacts (`last.pt`, `epoch*.pt`, `results.csv`, etc.)

## Expected Directory Structure After Training

```
models/
├── yolov8n.pt                    # ✅ Committed
└── custom_model/
    ├── weights/
    │   ├── best.pt               # ✅ Committed (after training)
    │   ├── last.pt               # ❌ Ignored (training artifact)
    │   └── epoch*.pt             # ❌ Ignored (checkpoints)
    ├── args.yaml                 # ❌ Ignored (training config)
    ├── results.csv               # ❌ Ignored (training metrics)
    └── results.png               # ❌ Ignored (plots)
```

## Model Performance Expectations

### Pre-trained YOLOv8n (COCO):
- General object detection
- 80 classes
- May detect deer as "sheep", "dog", or "horse" (closest COCO classes)
- Confidence: 40-60% on wildlife

### Custom Trained Model (Deer):
- **With 50 images**: 60-75% accuracy
- **With 100 images**: 75-85% accuracy
- **With 200+ images**: 85-95% accuracy
- Confidence: 70-90% on deer

## Testing Models

```bash
# Test pre-trained model
python backend/detector.py --model models/yolov8n.pt --source data/photos/

# Test custom model (after training)
python backend/test_custom_model.py \
    --model models/custom_model/weights/best.pt \
    --images data/training_data/images/val
```

## Troubleshooting

### Model not found
- Ensure `yolov8n.pt` exists (should be committed in git)
- For custom model: Check if `best.pt` was trained and committed
- Try: `git lfs pull` if using Git LFS for large files

### Out of memory during training
- Reduce batch size: `--batch 8` or `--batch 4`
- Use smaller model: `--model n` (nano) instead of `s` (small)
- Train on more powerful machine (NOT Raspberry Pi)

### Poor detection accuracy
- Need more training images (100+ recommended)
- Verify annotations with `visualize_annotations.py`
- Train for more epochs: `--epochs 100` or `--epochs 200`
- Use outdoor photos (not indoor scenes)
