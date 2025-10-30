# Practical Guide: Custom Model Training for Pi Yard Tracker

## The Real Process - Step by Step

This is the ACTUAL workflow you'll follow to train a custom model for any animal.

---

## Implementation Components

### Part 1: Data Collection System

### Part 2: Annotation Interface

### Part 3: Training Pipeline

### Part 4: Model Deployment

---

## Part 1: Data Collection System (DONE! ✅)

**You already have this!** Your camera capture script is collecting data.

### What You Need:

- **100-500 images** of the target animal (deer)
- **Variety**: Different times, angles, distances, lighting
- **Quality**: In-focus, clear subject

### Practical Collection Methods:

#### Method A: Use Your Existing System

```bash
# Point camera at yard, let it run
python backend/camera_capture.py

# Manually review photos later
# Keep photos with deer, delete rest
# Move good photos to training folder
```

#### Method B: Manual Photo Hunt

```bash
# Create training data folder
mkdir -p data/training_data/raw_images

# Copy/move deer photos here
# Can include photos from phone, other cameras, internet
```

#### Method C: Download Existing Dataset

```bash
# Use Roboflow Universe or similar
# Search: "deer", "white-tailed deer", etc.
# Download pre-labeled dataset
# Merge with your photos
```

**Recommended**: Mix of all three (50% online + 50% your photos)

---

## Part 2: Annotation Interface - The REAL Work

This is where you'll spend most time. You need to:

1. Draw boxes around animals
2. Label each box
3. Save in YOLO format

### Tool Options (Ranked by Ease of Use):

---

### ⭐ RECOMMENDED: Roboflow (Web-based, Easiest)

**Why**:

- No installation required
- Auto-suggests boxes (AI-assisted)
- Exports directly in YOLO format
- Free tier: 10,000 images
- Team collaboration built-in

**Process**:

1. **Sign up**: https://roboflow.com (free)

2. **Create Project**:

   ```
   Project Type: Object Detection
   Name: "NH Yard Wildlife"
   Classes: deer, turkey, rabbit (whatever you want)
   ```

3. **Upload Images**:

   - Drag & drop your photos
   - Bulk upload supported
   - Can upload videos (auto-extracts frames)

4. **Annotate** (Web interface):

   ```
   - Click image
   - Press 'B' or click box tool
   - Draw box around deer
   - Type label: "deer"
   - Press Enter
   - Next image

   Shortcuts:
   - 'D' = Next image
   - 'A' = Previous image
   - 'B' = Box tool
   - Delete = Remove box
   ```

5. **Smart Features**:

   - **Label Assist**: AI suggests boxes (you just confirm)
   - **Auto-label**: Upload 10 labeled images, AI labels the rest
   - **Keyboard shortcuts**: Very fast once you learn them

6. **Generate Dataset**:

   ```
   Format: YOLOv8
   Split: 70% train, 20% validation, 10% test
   Augmentation: (optional, adds variations)

   Download → You get a .zip with:
   - images/train/
   - images/val/
   - labels/train/
   - labels/val/
   - data.yaml
   ```

**Time**: ~1-2 minutes per image when you get fast

---

### Option 2: LabelImg (Desktop, Free, Offline)

**Why**:

- Completely offline
- Simple interface
- No account needed
- Open source

**Installation**:

```bash
# On your laptop/desktop (not Pi)
pip install labelImg

# Or on Pi if you want
cd /home/cjennison/src/pi-yard-tracker
source venv/bin/activate
pip install labelImg
```

**Usage**:

```bash
labelImg

# Or specify folder
labelImg data/training_data/raw_images
```

**Interface**:

```
┌─────────────────────────────────────┐
│ File  Edit  View  Help              │
├─────────────────────────────────────┤
│  [Open Dir] [Change Save Dir]       │
├─────────────────────────────────────┤
│                                      │
│     [Image displays here]            │
│                                      │
│     Draw boxes with mouse            │
│                                      │
├─────────────────────────────────────┤
│ Class: [deer ▼]                      │
│ Next (D) | Prev (A) | Save (Ctrl+S) │
└─────────────────────────────────────┘
```

**Shortcuts**:

- `W` = Draw box
- `D` = Next image
- `A` = Previous image
- `Ctrl+S` = Save
- `Del` = Delete box

**Workflow**:

1. Open directory with images
2. Press `W`, draw box around deer
3. Type "deer" in popup
4. Press `D` for next image
5. Repeat

**Output**: Creates `.txt` file next to each `.jpg`:

```
# yard_001.txt
0 0.5 0.6 0.3 0.4
# Format: class_id center_x center_y width height (normalized 0-1)
```

**Time**: ~2-3 minutes per image

---

### Option 3: CVAT (Advanced, Team Collaboration)

**Why**:

- Professional tool
- Video annotation
- Multi-user
- Self-hosted or cloud

**Setup**: More complex (Docker required)

**When to use**: If you have >1000 images or multiple people annotating

---

## Part 3: Training Pipeline - The Code

Now we need scripts to actually train the model.

### Training Environment Options:

#### Option A: Your Laptop/Desktop (RECOMMENDED)

**Why**: Faster training, easier debugging
**Time**: 1-2 hours for 50 epochs

#### Option B: Raspberry Pi

**Why**: You have it already
**Time**: 8-12 hours for 50 epochs
**⚠️ Not recommended**: Too slow

#### Option C: Google Colab (Free GPU)

**Why**: Free GPU access, fast training
**Time**: 30 minutes for 50 epochs
**✅ BEST for first-time training**

---

### Let me create the actual training scripts:
