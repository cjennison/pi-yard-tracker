# Python Script Workflow Guide

Complete Python-based workflow for custom deer detection model training.

## 📋 Overview

All operations are now managed through Python scripts - no manual terminal commands needed!

## 🛠️ Available Scripts

### 1. **cleanup_dataset.py** - Clean Training Data
```bash
# Remove everything (synthetic data, prepared dataset, models)
python backend/cleanup_dataset.py --all

# Only remove synthetic training images
python backend/cleanup_dataset.py --synthetic-only

# Only remove prepared YOLO dataset
python backend/cleanup_dataset.py --prepared-only

# Remove models only
python backend/cleanup_dataset.py --models-only
```

### 2. **generate_training_data.py** - Generate Synthetic Images
```bash
# Scene-matching with your outdoor photo (RECOMMENDED)
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --base-image photos/backyard.jpg \
    --count 100

# Generate from scratch with outdoor description
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --background "outdoor meadow with grass and trees" \
    --count 50
```

**Features:**
- ✅ Automatic bounding box detection using pre-trained YOLO
- ✅ Scene-matching based on your actual backyard photos
- ✅ GPT-4o Vision analyzes scene lighting, weather, time of day
- ✅ DALL-E 3 generates matching images with deer
- ✅ Auto-saves images + YOLO format annotations

### 3. **prepare_dataset.py** - Organize Dataset
```bash
# Prepare dataset with 70/20/10 train/val/test split
python backend/prepare_dataset.py \
    --input data/synthetic_training \
    --output data/training_data \
    --split 70 20 10 \
    --clean

# Custom split (80/15/5)
python backend/prepare_dataset.py \
    --split 80 15 5 \
    --seed 42
```

**Features:**
- ✅ Creates proper YOLO directory structure
- ✅ Randomly shuffles and splits data
- ✅ Validates image-label pairs
- ✅ Reproducible splits with seed
- ✅ Logging throughout

### 4. **visualize_annotations.py** - Verify Annotations
```bash
# Visualize training set annotations
python backend/visualize_annotations.py \
    --images-dir data/training_data/images/train \
    --labels-dir data/training_data/labels/train \
    --output-dir data/annotation_check \
    --sample-size 10

# Visualize all synthetic data
python backend/visualize_annotations.py \
    --images-dir data/synthetic_training \
    --labels-dir data/synthetic_training
```

**Features:**
- ✅ Draws green bounding boxes on images
- ✅ Verifies auto-annotations are correct
- ✅ Sample or visualize all images
- ✅ Saves to separate directory

### 5. **train_custom_model.py** - Train Model
```bash
# Train with default settings (50 epochs)
python backend/train_custom_model.py \
    --dataset data/deer_dataset.yaml

# Train with more epochs and larger batch
python backend/train_custom_model.py \
    --dataset data/deer_dataset.yaml \
    --epochs 100 \
    --batch 32 \
    --imgsz 640
```

**Features:**
- ✅ Transfer learning from YOLOv8n
- ✅ Automatic augmentation
- ✅ Progress tracking
- ✅ Saves best model to `models/custom_model/weights/best.pt`

### 6. **test_custom_model.py** - Test Model
```bash
# Test on validation images
python backend/test_custom_model.py \
    --model models/custom_model/weights/best.pt \
    --images-dir data/training_data/images/val \
    --conf 0.25 \
    --save-results

# Test on new outdoor photos
python backend/test_custom_model.py \
    --model models/custom_model/weights/best.pt \
    --images-dir photos/test_images \
    --conf 0.25
```

**Features:**
- ✅ Tests on directory of images
- ✅ Configurable confidence threshold
- ✅ Saves results with bounding boxes
- ✅ Prints detection statistics

### 7. **workflow.py** - Complete Pipeline (ALL-IN-ONE!)
```bash
# Full workflow with outdoor base image (RECOMMENDED)
python backend/workflow.py \
    --base-image photos/backyard.jpg \
    --count 100 \
    --epochs 100

# Full workflow generating from scratch
python backend/workflow.py \
    --background "outdoor meadow with grass" \
    --count 50 \
    --epochs 50

# Just generate and prepare (skip training)
python backend/workflow.py \
    --count 50 \
    --skip-training

# Resume training with existing data
python backend/workflow.py \
    --skip-generation \
    --skip-preparation \
    --epochs 100
```

**Features:**
- ✅ Runs entire pipeline automatically
- ✅ Step-by-step logging
- ✅ Time tracking for each step
- ✅ Skip individual steps
- ✅ Continue on error option

## 🚀 Quick Start Workflows

### Workflow A: Fresh Start with Outdoor Photos (RECOMMENDED)

```bash
# Step 1: Clean everything
python backend/cleanup_dataset.py --all

# Step 2: Run complete workflow
python backend/workflow.py \
    --base-image photos/backyard1.jpg \
    --count 100 \
    --epochs 100 \
    --clean
```

**That's it!** The workflow script will:
1. Generate 100 synthetic deer images based on your backyard
2. Auto-detect deer positions with YOLO
3. Split into train/val/test (70/20/10)
4. Visualize 5 sample annotations
5. Train model for 100 epochs
6. Test on validation set

### Workflow B: Fresh Start from Scratch (Faster)

```bash
# Step 1: Clean everything
python backend/cleanup_dataset.py --all

# Step 2: Run complete workflow
python backend/workflow.py \
    --background "outdoor meadow with grass and trees at sunset" \
    --count 50 \
    --epochs 50 \
    --clean
```

### Workflow C: Step-by-Step Manual Control

```bash
# Step 1: Clean
python backend/cleanup_dataset.py --all

# Step 2: Generate data
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --base-image photos/backyard.jpg \
    --count 100

# Step 3: Check a few annotations visually
python backend/visualize_annotations.py \
    --images-dir data/synthetic_training \
    --labels-dir data/synthetic_training \
    --sample-size 5

# Step 4: Prepare dataset
python backend/prepare_dataset.py \
    --input data/synthetic_training \
    --output data/training_data \
    --split 70 20 10 \
    --clean

# Step 5: Train
python backend/train_custom_model.py \
    --dataset data/deer_dataset.yaml \
    --epochs 100

# Step 6: Test
python backend/test_custom_model.py \
    --model models/custom_model/weights/best.pt \
    --images-dir data/training_data/images/val \
    --save-results
```

## 📊 Expected Results

### Small Dataset (50 images)
- Training time: ~5-10 minutes
- Expected accuracy: 60-75%
- Detection rate: 40-60%
- **Note:** May overfit or have poor generalization

### Medium Dataset (100 images)
- Training time: ~10-20 minutes
- Expected accuracy: 75-85%
- Detection rate: 60-75%
- **Recommended minimum for real use**

### Large Dataset (200+ images)
- Training time: ~20-40 minutes
- Expected accuracy: 85-95%
- Detection rate: 75-90%
- **Best results, production quality**

## 💡 Best Practices

### 1. Use Outdoor Base Photos
- ❌ Don't use indoor office photos
- ✅ Use actual backyard photos (where you'll deploy)
- ✅ Include variety: different times of day, weather, seasons

### 2. Generate Sufficient Data
- ❌ Don't train on <20 images (will overfit)
- ✅ Generate 100+ images for good results
- ✅ More data = better generalization

### 3. Verify Annotations
- ✅ Always run `visualize_annotations.py` before training
- ✅ Check that bounding boxes match deer positions
- ✅ If wrong, regenerate with different prompts

### 4. Monitor Training
- ✅ Watch for loss plateauing (indicates convergence)
- ✅ Stop early if validation accuracy stops improving
- ✅ Check for overfitting (training acc >> validation acc)

### 5. Test Thoroughly
- ✅ Test on validation set first
- ✅ Then test on completely new outdoor photos
- ✅ Adjust confidence threshold based on results

## 🎯 Next Steps After Training

Once you have a working model:

1. **Deploy to capture system:**
   ```bash
   # Update capture_images.py to use custom model
   python backend/capture_images.py --custom-model
   ```

2. **Monitor performance:**
   - Check detections in `data/captures/`
   - Look for false positives/negatives
   - Generate more training data if needed

3. **Iterate and improve:**
   - Add more training data over time
   - Retrain periodically with new images
   - Fine-tune confidence thresholds

## 📁 Directory Structure

After running workflow:

```
pi-yard-tracker/
├── backend/
│   ├── cleanup_dataset.py          # Clean datasets
│   ├── generate_training_data.py   # Generate synthetic images
│   ├── prepare_dataset.py          # Split train/val/test
│   ├── visualize_annotations.py    # Verify annotations
│   ├── train_custom_model.py       # Train model
│   ├── test_custom_model.py        # Test model
│   └── workflow.py                 # ALL-IN-ONE script
├── data/
│   ├── synthetic_training/         # Generated images + labels
│   ├── training_data/              # Prepared dataset
│   │   ├── images/
│   │   │   ├── train/
│   │   │   ├── val/
│   │   │   └── test/
│   │   └── labels/
│   │       ├── train/
│   │       ├── val/
│   │       └── test/
│   └── annotation_check/           # Visualization output
├── models/
│   └── custom_model/
│       └── weights/
│           └── best.pt             # Trained model
└── photos/                         # Your base images
    └── backyard*.jpg
```

## 🔧 Troubleshooting

### "OpenAI API error"
- Check `.env` file has valid `OPENAI_API_KEY`
- Ensure API key has billing enabled
- Check API usage limits

### "No images found"
- Verify images are in correct directory
- Check file extensions (.jpg, .png)
- Run with `--input` flag pointing to correct path

### "Training fails immediately"
- Check dataset YAML paths are absolute
- Verify train/val/test directories exist and have images
- Try smaller batch size (`--batch 8`)

### "Poor detection rate"
- Need more training data (100+ images)
- Try more epochs (`--epochs 100`)
- Use outdoor base images (not indoor)
- Verify annotations are correct with visualize_annotations.py

### "Model not found"
- Check `models/custom_model/weights/best.pt` exists
- Ensure training completed successfully
- Look for errors in training logs

## 📞 Support

See full documentation in:
- `docs/SYNTHETIC_DATA_GENERATION.md` - Detailed generation guide
- `docs/QUICK_START_TRAINING.md` - Training workflow
- `README.md` - Project overview

---

**Remember:** All operations are now Python scripts - no terminal command memorization needed! 🎉
