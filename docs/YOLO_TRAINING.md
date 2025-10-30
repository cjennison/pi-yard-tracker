# YOLO Training Guide - Custom Animal Detection

## Understanding YOLO Training

### Pre-trained vs Custom Models

#### ✅ What YOLO Already Knows (COCO Dataset - 80 Classes)

**Animals in COCO:**

- bird
- cat
- dog
- horse
- sheep
- cow
- elephant
- bear
- zebra
- giraffe

**NOT in COCO (need custom training):**

- ❌ deer / moose / elk
- ❌ rabbit / squirrel / chipmunk
- ❌ fox / coyote / wolf
- ❌ raccoon / opossum / skunk
- ❌ turkey / chicken / duck (specific birds)
- ❌ Specific species (e.g., "White-tailed deer" vs "Mule deer")

### Training Process Overview

```
1. Collect Images        →  2. Label/Annotate    →  3. Train Model  →  4. Deploy
   (100-1000+ photos)        (Draw boxes, label)      (Fine-tune YOLO)    (Use on Pi)
   ↓                         ↓                         ↓                   ↓
   Your yard photos          "This is a deer"          Learning process    Detect in real-time
```

## Step-by-Step: Training YOLO for New Hampshire Deer

### Option 1: Use Pre-trained Model (Quick Start)

First, we'll use YOLO's pre-trained model to detect common animals. This works immediately.

### Option 2: Custom Training (Advanced)

Then, we'll train a custom model to recognize specific animals.

---

## Detailed Training Process

### 1. Data Collection (100-500 images minimum)

**Option A: Collect Your Own**

```python
# Use the camera capture system to collect images automatically!
# Point camera at yard, let it run for a few days
# Manually review and save images with deer

# Result: data/training_images/deer/*.jpg
```

**Option B: Use Existing Datasets**

- [Roboflow Universe](https://universe.roboflow.com/) - Pre-labeled datasets
- [Open Images Dataset](https://storage.googleapis.com/openimages/web/index.html) - Google's dataset
- [iNaturalist](https://www.inaturalist.org/) - Wildlife observations

**Best Practice: Mix both!**

- 70% existing datasets (for general "deer" knowledge)
- 30% your yard images (for your specific camera angle/lighting)

### 2. Image Annotation (Labeling)

You need to draw boxes around animals and label them. Use one of these tools:

#### Recommended: LabelImg (Free, Easy)

```bash
# Install
pip install labelImg

# Run
labelImg

# Instructions:
# 1. Open Dir → Select your images folder
# 2. Press 'W' to draw box around deer
# 3. Type label: "deer" or "white-tailed-deer"
# 4. Press 'D' to go to next image
# 5. Saves .txt files in YOLO format
```

#### Alternative: Roboflow (Web-based, Free tier)

- Upload images to roboflow.com
- Draw boxes in browser
- Auto-generates train/validation split
- Exports in YOLO format

**Annotation Format (YOLO):**

```
# File: deer_001.txt (one per image)
# Format: class_id x_center y_center width height (all normalized 0-1)
0 0.5 0.6 0.3 0.4

# Means: Class 0 (deer), centered at 50% width, 60% height,
#        box is 30% of image width, 40% of image height
```

### 3. Dataset Organization

```
data/
└── training_data/
    ├── images/
    │   ├── train/          # 80% of images
    │   │   ├── deer_001.jpg
    │   │   ├── deer_002.jpg
    │   │   └── ...
    │   └── val/            # 20% of images
    │       ├── deer_050.jpg
    │       └── ...
    └── labels/
        ├── train/          # Matching .txt files
        │   ├── deer_001.txt
        │   ├── deer_002.txt
        │   └── ...
        └── val/
            ├── deer_050.txt
            └── ...
```

### 4. Create Dataset Configuration

```yaml
# data/deer_dataset.yaml

# Paths (absolute or relative to this file)
path: /home/cjennison/src/pi-yard-tracker/data/training_data
train: images/train
val: images/val

# Classes
nc: 3 # number of classes
names: ["deer", "turkey", "rabbit"] # Your custom animals

# Optional: Use pre-trained weights as starting point
# This is called "transfer learning" - much faster!
```

### 5. Training Script

```python
# backend/train_model.py

from ultralytics import YOLO
import os

def train_custom_model():
    """Train custom YOLO model for New Hampshire wildlife"""

    # Load pre-trained YOLOv8n as starting point
    # This is MUCH faster than training from scratch
    # Model already knows what "animal-like" features look like
    model = YOLO('yolov8n.pt')

    # Fine-tune on your custom dataset
    results = model.train(
        data='data/deer_dataset.yaml',
        epochs=50,              # How many times to see each image
        imgsz=640,              # Image size (larger = more accurate, slower)
        batch=16,               # Images per training step
        device='cpu',           # Use 'cuda' if you have GPU
        patience=10,            # Stop if no improvement for 10 epochs
        project='models',
        name='nh_wildlife',

        # Transfer learning settings
        pretrained=True,        # Start from pre-trained weights
        freeze=10,              # Freeze first 10 layers (speed up training)
    )

    # Model saved to: models/nh_wildlife/weights/best.pt
    print(f"✅ Training complete!")
    print(f"📊 Best model saved to: {results.save_dir}/weights/best.pt")

if __name__ == "__main__":
    train_custom_model()
```

### 6. Training Performance Expectations

**On Raspberry Pi 5:**

- ⚠️ **Not recommended** for training (too slow)
- Training 50 epochs on 200 images: ~8-12 hours
- Better to train on laptop/desktop

**On Laptop/Desktop (with GPU):**

- ✅ **Recommended**
- NVIDIA GPU: ~30-60 minutes for 50 epochs
- CPU only: ~2-4 hours

**Best Approach:**

1. Train on your laptop/desktop
2. Copy trained model file (`best.pt`) to Raspberry Pi
3. Pi only does **inference** (running the model), not training

### 7. Using Your Custom Model

```python
# backend/detector.py

from ultralytics import YOLO

# Load your custom model instead of pre-trained
model = YOLO('models/nh_wildlife/weights/best.pt')

# Use it exactly like pre-trained model
results = model.predict('photo.jpg', conf=0.5)

# Results now include YOUR custom classes
for result in results:
    for box in result.boxes:
        class_name = result.names[int(box.cls)]  # 'deer', 'turkey', etc.
        confidence = float(box.conf)
        print(f"Detected: {class_name} ({confidence:.2%})")
```

---

## Transfer Learning: The Secret Sauce 🎯

### Why Training is Fast(er)

**Training from Scratch:**

```
Start: Model knows NOTHING
↓
Learn: What is an edge? What is a shape? What is fur? What is an animal?
↓
Result: 100+ hours of training needed
```

**Transfer Learning (What we do):**

```
Start: Model already knows animals, shapes, textures from COCO
↓
Learn: "This specific pattern = deer" (fine-tuning)
↓
Result: 1-2 hours of training needed
```

**Analogy:**

- From scratch = Teaching someone who's never seen an animal to recognize deer
- Transfer learning = Teaching a dog expert to recognize deer (they already know "animal")

### What Gets "Frozen" vs "Trained"

```
YOLOv8 Architecture:
┌─────────────────────────┐
│ Layer 1-10: Basic Features │ ← FROZEN (reuse pre-trained)
│ (edges, textures, shapes)  │
├─────────────────────────┤
│ Layer 11-20: Mid Features  │ ← PARTIALLY TRAINED
│ (animal parts, patterns)   │
├─────────────────────────┤
│ Layer 21-30: High Features │ ← FULLY TRAINED
│ (specific animals)         │
└─────────────────────────┘
```

---

## Practical Recommendations

### Scenario 1: "I just want to track any animals"

**Solution:** Use pre-trained YOLOv8n

- Detects: dogs, cats, birds, people, bears, horses
- No training needed
- Works immediately

### Scenario 2: "I want to track deer specifically"

**Solution:** Custom training

1. Collect 100-300 deer images (Roboflow + your yard)
2. Annotate with LabelImg (~2-4 hours)
3. Train on laptop (1-2 hours)
4. Deploy to Pi

### Scenario 3: "I want to distinguish species"

**Solution:** Advanced custom training

- Classes: `white-tailed-deer`, `moose`, `black-bear`, `coyote`
- Need 200-500 images per class
- More epochs (100-200)
- Potentially larger model (YOLOv8s instead of YOLOv8n)

---

## Educational: How YOLO "Learns"

### Neural Network Basics

```python
# Simplified version of what happens during training

for epoch in range(50):
    for image, label in training_data:
        # 1. Model makes a prediction
        prediction = model(image)  # "I see a deer at (100, 200)"

        # 2. Compare to correct answer
        error = prediction - actual_label  # "Off by 10 pixels!"

        # 3. Adjust model weights to reduce error
        model.weights -= learning_rate * error.gradient

        # Over time, predictions get closer to correct answers
```

### What Makes a Good Dataset

**Quality > Quantity:**

- ✅ 200 diverse, well-labeled images > 1000 similar, poorly-labeled images

**Diversity matters:**

- Different times of day (morning, afternoon, evening)
- Different weather (sunny, cloudy, rain)
- Different angles (front, side, far, close)
- Different poses (standing, walking, eating)

**Common mistakes:**

- ❌ All images from same camera angle
- ❌ All images at same time of day
- ❌ Boxes too tight or too loose
- ❌ Missing small animals in background

---

## Cost & Time Estimates

### Pre-trained Model

- **Cost:** $0 (model is free)
- **Time:** 15 minutes to download and test
- **Accuracy:** Good for common animals (80-95%)

### Custom Training

- **Cost:** $0 (all tools are free)
- **Time Breakdown:**
  - Image collection: 2-10 hours (mostly waiting)
  - Annotation: 2-4 hours (100 images × 1-2 min each)
  - Training: 1-2 hours (on laptop with GPU)
  - Testing/tuning: 1-2 hours
  - **Total:** 6-18 hours
- **Accuracy:** Excellent for your specific animals (90-98%)

### Ongoing Improvement

- Collect more images over time
- Re-train monthly with new data
- Model gets better as dataset grows

---

## Implementation Approaches

We'll implement BOTH approaches:

### Approach 1: Quick Win

1. Install YOLOv8n pre-trained
2. Detect animals immediately
3. See what works out-of-the-box

### Approach 2: Custom Training

1. Create annotation tools integration
2. Build training script
3. Instructions for training on laptop
4. Deploy custom model to Pi

This gives you a working system NOW, with path to improvement LATER!

---

## Tools & Resources

### Annotation Tools

- **LabelImg**: https://github.com/heartexlabs/labelImg
- **Roboflow**: https://roboflow.com/ (web-based)
- **CVAT**: https://cvat.ai/ (advanced, team collaboration)

### Datasets

- **Roboflow Universe**: https://universe.roboflow.com/
- **Open Images**: https://storage.googleapis.com/openimages/web/index.html
- **iNaturalist**: https://www.inaturalist.org/

### Training Resources

- **Ultralytics Docs**: https://docs.ultralytics.com/modes/train/
- **YOLOv8 Tutorial**: https://docs.ultralytics.com/quickstart/

### Hardware Recommendations

- **For Training**: Desktop/Laptop with NVIDIA GPU (GTX 1060 or better)
- **For Inference**: Raspberry Pi 4/5 (CPU is fine)
- **Cloud Option**: Google Colab (free GPU access)

---

**Ready to start with pre-trained model, then add custom training capability?**
