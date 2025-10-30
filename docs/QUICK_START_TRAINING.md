# Quick Start: Train Your Custom Deer Detector

**Goal:** Train a custom model to detect deer in YOUR yard in under 3 hours.

## The Revolutionary Approach

Instead of manually collecting 1000 deer photos, we'll:

1. ✅ Use YOUR actual backyard photos as backgrounds
2. ✅ Have AI insert realistic deer into them
3. ✅ Automatically create YOLO annotations
4. ✅ Train a custom model

**Total cost:** ~$10-20 for 500 training images
**Total time:** 2-3 hours (mostly automated)

## Prerequisites

```bash
# 1. OpenAI API key
# Get from: https://platform.openai.com/api-keys
# Add to .env file:
OPENAI_API_KEY=sk-your-key-here

# 2. Dependencies installed
source venv/bin/activate
pip install openai python-dotenv requests
```

## Step-by-Step Guide

### Step 1: Capture Base Photos (10 minutes)

```bash
# Option A: Use existing photos from your camera
# You already have these from the camera capture system!
ls data/photos/*.jpg

# Option B: Take fresh photos
# - 3-5 different angles of your backyard
# - Different times of day (morning, afternoon, evening)
# - Different weather if possible
# Save to: data/photos/base/
```

### Step 2: Test Generation (5 minutes)

```bash
# Generate 1 test image to verify it works
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --base-image data/photos/yard_20251028_204701_372.jpg \
    --count 1

# Check the result
ls -lh data/synthetic_training/

# View the image - it should show a deer in your backyard!
```

### Step 3: Generate Training Dataset (1-2 hours)

```bash
# Strategy: Generate 50-100 images per base photo
# With 3 base photos = 150-300 total images

# Using your existing photo
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --base-image data/photos/yard_20251028_204701_372.jpg \
    --count 50

# This will:
# - Take ~2 hours (50 images x 2 min each)
# - Cost ~$1.00 (50 x $0.02)
# - Generate 50 images + 50 annotations

# Repeat with other angles if you have them
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --base-image data/photos/yard_20251028_204703_104.jpg \
    --count 50
```

### Step 4: Organize for YOLO Training (10 minutes)

```bash
# Create YOLO folder structure
bash scripts/setup_training_data.sh

# This creates:
# data/images/train/
# data/images/val/
# data/images/test/
# data/labels/train/
# data/labels/val/
# data/labels/test/

# Now split your synthetic images (70/20/10 split)
# For 100 images: 70 train, 20 val, 10 test

# Move first 70 images to train
mv data/synthetic_training/synthetic_*.jpg data/images/train/ | head -70
mv data/synthetic_training/synthetic_*.txt data/labels/train/ | head -70

# Move next 20 to val
mv data/synthetic_training/synthetic_*.jpg data/images/val/ | head -20
mv data/synthetic_training/synthetic_*.txt data/labels/val/ | head -20

# Move last 10 to test
mv data/synthetic_training/synthetic_*.jpg data/images/test/
mv data/synthetic_training/synthetic_*.txt data/labels/test/
```

### Step 5: Configure Dataset (2 minutes)

```bash
# Copy example config
cp data/deer_dataset.yaml.example data/deer_dataset.yaml

# Edit if needed (should work as-is for deer)
# Verify paths point to data/images/ and data/labels/
```

### Step 6: Train Model (30-60 minutes)

```bash
# Train on laptop (recommended) or Pi
python backend/train_custom_model.py \
    --dataset data/deer_dataset.yaml \
    --epochs 50 \
    --model n \
    --batch 16

# Training will:
# - Use transfer learning (starts from pre-trained YOLOv8n)
# - Take 30-60 minutes on laptop (2-4 hours on Pi)
# - Save checkpoints every 10 epochs
# - Save best model to: models/custom_model/weights/best.pt

# Watch progress:
# - Loss should decrease
# - mAP (accuracy) should increase
# - Patience: 20 epochs without improvement = early stop
```

### Step 7: Test Your Model (5 minutes)

```bash
# Test on new images
python backend/test_custom_model.py \
    --model models/custom_model/weights/best.pt \
    --images data/photos/ \
    --confidence 0.5

# This will:
# - Run inference on all photos in data/photos/
# - Save visualizations with bounding boxes
# - Print detection statistics

# Check results in:
# data/photos/detections_custom/
```

### Step 8: Deploy to Camera System (2 minutes)

```bash
# Edit backend/camera_capture.py
# Change line ~30:
# MODEL_PATH = "models/yolov8n.pt"
# to:
# MODEL_PATH = "models/custom_model/weights/best.pt"

# Run camera with custom model!
python backend/camera_capture.py

# Your camera now detects DEER specifically! 🦌
```

## Expected Results

After training on 100-200 synthetic images:

- **Accuracy:** 70-85% detection rate
- **False positives:** Low (model trained on YOUR backyard)
- **Inference time:** ~420ms (same as pre-trained model)

## Troubleshooting

### "OpenAI API key not found"

```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Should show: OPENAI_API_KEY=sk-...
# If not, add it:
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

### "Base image not found"

```bash
# Verify file exists
ls -l data/photos/yard_20251028_204701_372.jpg

# Use absolute path if needed
python backend/generate_training_data.py \
    --base-image /home/cjennison/src/pi-yard-tracker/data/photos/yard_20251028_204701_372.jpg \
    --object "deer" \
    --count 1
```

### Generated deer looks fake

```bash
# Try different prompts
--object "realistic white-tailed deer"
--object "photorealistic white-tailed deer in natural pose"

# Or adjust your base image:
# - Use well-lit photos
# - Avoid shadows/dark areas where deer would be placed
# - Use photos with clear background
```

### Training accuracy is low

```bash
# Generate more images (aim for 200-500)
# Mix with real photos if you have any
# Increase training epochs:
python backend/train_custom_model.py --epochs 100

# Check your annotations are correct:
# Use LabelImg to review some samples
```

## Cost Calculator

| Images | Cost (Edit Mode) | Time      | Training Time |
| ------ | ---------------- | --------- | ------------- |
| 50     | $1.00            | ~2 hours  | 20-30 min     |
| 100    | $2.00            | ~4 hours  | 30-45 min     |
| 200    | $4.00            | ~8 hours  | 45-60 min     |
| 500    | $10.00           | ~20 hours | 1-2 hours     |

**Recommended:** Start with 50-100 images, test model, generate more if needed.

## Tips for Best Results

1. **Use multiple base photos** - Different angles improve generalization
2. **Vary the prompts** - "deer walking", "deer standing", "deer eating grass"
3. **Mix synthetic + real** - If you capture any real deer, add them!
4. **Review first 10 images** - Make sure quality is good before generating 100s
5. **Train on laptop** - Much faster than Pi (30 min vs 4 hours)
6. **Monitor training** - Watch for overfitting (validation loss increases)

## Next Steps After Training

1. **Test in production** - Run camera_capture.py with custom model
2. **Collect edge cases** - Save images where model fails
3. **Iterative improvement** - Generate more training data for edge cases
4. **Add more animals** - Turkey, rabbit, fox (new class IDs)
5. **Database integration** - Store all detections in SQLite
6. **Web UI** - View timeline of animal visits

---

**You now have a systematic, repeatable process to train custom models for ANY animal!** 🎉

**Created:** October 28, 2025
