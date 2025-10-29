# Training Module

Custom YOLO model training pipeline. **Must run on powerful machine with GPU.**

## Scripts

### `generate_training_data.py`
Generate synthetic training images using OpenAI DALL-E 3.

**Usage:**
```bash
# From scratch
python backend/training/generate_training_data.py \
    --object "white-tailed deer" \
    --background "outdoor backyard" \
    --count 100

# Scene matching
python backend/training/generate_training_data.py \
    --object "white-tailed deer" \
    --base-image photos/backyard.jpg \
    --count 100
```

### `prepare_dataset.py`
Organize images into YOLO train/val/test structure.

**Usage:**
```bash
python backend/training/prepare_dataset.py \
    --input data/synthetic_training \
    --output data/training_data \
    --split 70 20 10
```

### `train_custom_model.py`
Train custom YOLO model with transfer learning.

**Usage:**
```bash
python backend/training/train_custom_model.py \
    --dataset data/deer_dataset.yaml \
    --epochs 100 \
    --batch 16
```

⚠️ **Requires GPU machine** - will kill Raspberry Pi!

### `test_custom_model.py`
Test trained model on validation images.

**Usage:**
```bash
python backend/training/test_custom_model.py \
    --model models/custom_model/weights/best.pt \
    --images data/training_data/images/val
```

### `visualize_annotations.py`
Draw bounding boxes to verify annotations.

**Usage:**
```bash
python backend/training/visualize_annotations.py \
    --input data/synthetic_training \
    --output data/annotation_check
```

### `cleanup_dataset.py`
Remove training data and models.

**Usage:**
```bash
python backend/training/cleanup_dataset.py --all
```

### `workflow.py`
Complete end-to-end training pipeline.

**Usage:**
```bash
python backend/training/workflow.py \
    --base-image photos/backyard.jpg \
    --count 100 \
    --epochs 100
```

## Workflow

1. Generate synthetic data → 2. Prepare dataset → 3. Visualize annotations → 4. Train model → 5. Test model

See [docs/PYTHON_WORKFLOW.md](../../docs/PYTHON_WORKFLOW.md) for details.
