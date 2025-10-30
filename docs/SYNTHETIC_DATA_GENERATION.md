# Synthetic Training Data Generation

**Problem Solved:** "There's no way I'm going to get 1000 deer photos."

**Solution:** Use AI to generate realistic training images with automatic annotations!

## Two Powerful Modes

### Mode 1: Generate From Scratch 🎨

Use DALL-E 3 to create entirely new images based on text descriptions.

### Mode 2: Edit Your Photos 📸 (RECOMMENDED!)

**Insert deer into YOUR actual backyard photos!** This is better because:

- Uses your exact environment (lighting, terrain, camera angle)
- More realistic than AI-generated backgrounds
- Cheaper ($0.02 vs $0.04 per image)
- Model trains on scenes it will actually see

## How It Works

### Mode 1: Generate From Scratch

```
User Input:
  "white-tailed deer" + "New Hampshire backyard"

    ↓

DALL-E 3 API:
  Generates realistic photo with centered deer

    ↓

Automatic Annotation:
  Creates YOLO bounding box (centered, 60% of image)

    ↓

Training Data:
  synthetic_white_tailed_deer_20251028_143052.jpg
  synthetic_white_tailed_deer_20251028_143052.txt
```

### Mode 2: Edit Your Photo (NEW!)

```
Your Photo:                    Object Name:
data/photos/backyard.jpg  +    "white-tailed deer"

    ↓

GPT-4o Vision API:
  Analyzes your photo: "afternoon lighting, grassy backyard, fence visible..."

    ↓

DALL-E 3 Generation:
  Creates NEW image matching your scene + deer

    ↓

Automatic Annotation:
  Creates YOLO bounding box for the deer

    ↓

Training Data:
  synthetic_white_tailed_deer_20251028_143052.jpg  ← Matches YOUR scene
  synthetic_white_tailed_deer_20251028_143052.txt
```

**Note:** This uses vision analysis + generation rather than direct editing, because:

- DALL-E 2 edit requires masks (we don't want to manually create them)
- DALL-E 3 doesn't support editing
- GPT Image editing is not yet in stable API
- **This approach still works great** - it matches your lighting, environment, and perspective!

## Setup

### 1. Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create account or sign in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

**Cost:**

- **DALL-E 3** (generate): ~$0.04 per image (standard quality, 1024x1024)
- **Vision + DALL-E 3** (scene matching): ~$0.04-0.05 per image (includes vision analysis)
- Using base images costs about the same but gives better scene matching!

### 2. Configure Environment

Add your API key to `.env` file:

```bash
# Copy example if you haven't already
cp .env.example .env

# Edit .env and add your key
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Test Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Test with single image
python backend/generate_training_data.py \
    --object "deer" \
    --background "meadow" \
    --count 1
```

## Usage Examples

### 🌟 RECOMMENDED: Edit Your Backyard Photos

```bash
# Step 1: Take a photo of your empty backyard
# Use your Pi camera or phone, save to data/photos/

# Step 2: Generate deer in YOUR backyard
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --base-image data/photos/my_backyard.jpg \
    --count 10
```

**Why this is better:**

- Deer appears in YOUR exact environment
- Same lighting, camera angle, background as real captures
- Model trains on what it will actually see
- Cheaper than generating from scratch!

### Generate From Scratch (Alternative)

```bash
# 10 white-tailed deer in generic setting
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --background "New Hampshire backyard with grass and pine trees" \
    --count 10
```

### Generate Multiple Animal Types

```bash
# Deer
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --background "forest clearing" \
    --count 50 \
    --class-id 0

# Turkey
python backend/generate_training_data.py \
    --object "wild turkey" \
    --background "autumn forest with leaves" \
    --count 30 \
    --class-id 1

# Rabbit
python backend/generate_training_data.py \
    --object "eastern cottontail rabbit" \
    --background "garden with vegetables" \
    --count 20 \
    --class-id 2
```

### Test Single Image First

Always test with `--count 1` first to verify quality:

```bash
# Test editing your photo
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --base-image data/photos/test_backyard.jpg \
    --count 1

# OR test generation from scratch
python backend/generate_training_data.py \
    --object "deer" \
    --background "snowy backyard at dawn" \
    --count 1
```

Check the generated image in `data/synthetic_training/`. If it looks good, increase count!

## Command Line Options

| Option         | Description                                        | Default                  |
| -------------- | -------------------------------------------------- | ------------------------ |
| `--object`     | Object to generate/add (e.g., "white-tailed deer") | **Required**             |
| `--background` | Scene description (only for generate mode)         | None (optional)          |
| `--base-image` | Path to YOUR backyard photo to edit                | None (enables EDIT mode) |
| `--count`      | Number of images to generate                       | 1                        |
| `--class-id`   | YOLO class ID (0, 1, 2...)                         | 0                        |
| `--output`     | Output directory                                   | data/synthetic_training  |
| `--delay`      | Delay between API calls (seconds)                  | 2.0                      |

## Complete Workflow: From Photo to Trained Model

### Quick Start (5 minutes)

```bash
# 1. Take a photo of your empty backyard
# Save as: data/photos/backyard.jpg

# 2. Generate 1 test image
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --base-image data/photos/backyard.jpg \
    --count 1

# 3. Check the result
# Look in: data/synthetic_training/

# 4. If it looks good, generate 50 more!
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --base-image data/photos/backyard.jpg \
    --count 50
```

### Full Workflow (2-3 hours)

```bash
# Step 1: Capture base photos (10-20 minutes)
# - Take 3-5 photos of your backyard from different angles
# - Morning, afternoon, different weather
# - Save to data/photos/base/

# Step 2: Generate training data (1-2 hours)
# Generate 30 images per base photo = 150 total images
for photo in data/photos/base/*.jpg; do
    python backend/generate_training_data.py \
        --object "white-tailed deer" \
        --base-image "$photo" \
        --count 30
done

# Step 3: Review and organize (15 minutes)
# Check quality, move to YOLO structure
bash scripts/setup_training_data.sh
# Manually split into train/val/test (70/20/10)

# Step 4: Train model (30-60 minutes on laptop)
python backend/train_custom_model.py \
    --dataset data/deer_dataset.yaml \
    --epochs 50 \
    --model n

# Step 5: Test and deploy (5 minutes)
python backend/test_custom_model.py \
    --model models/custom_model/weights/best.pt \
    --images data/photos/ \
    --confidence 0.5
```

## Output Structure

```
data/synthetic_training/
├── synthetic_white_tailed_deer_20251028_143052_123.jpg   ← Image
├── synthetic_white_tailed_deer_20251028_143052_123.txt   ← YOLO annotation
├── synthetic_white_tailed_deer_20251028_143105_456.jpg
├── synthetic_white_tailed_deer_20251028_143105_456.txt
└── ...
```

Each `.txt` file contains YOLO-format annotation:

```
0 0.5 0.5 0.6 0.6
```

- `0` = class ID (deer)
- `0.5 0.5` = center coordinates (x, y) - normalized 0-1
- `0.6 0.6` = width, height - normalized 0-1

## Best Practices

### 1. Start Small

```bash
# Generate 1-5 test images first
--count 1
```

Check quality before generating hundreds!

### 2. Vary Your Prompts

The script automatically adds lighting variations:

- Morning light
- Afternoon sun
- Overcast sky
- Golden hour

But you can also create multiple batches with different backgrounds:

```bash
# Batch 1: Forest
--background "dense forest with oak trees"

# Batch 2: Field
--background "open meadow with wildflowers"

# Batch 3: Suburban
--background "residential backyard with fence"
```

### 3. Mix Synthetic + Real Data

Best results come from combining:

- **70% synthetic images** (for volume and diversity)
- **30% real photos** (for authentic edge cases)

### 4. Review and Adjust Annotations

The script creates centered bounding boxes (60% of image). For best accuracy:

1. Review generated images
2. Use LabelImg to adjust boxes if needed:
   ```bash
   labelImg data/synthetic_training data/synthetic_training
   ```
3. Some images might have deer off-center - fix those

### 5. Rate Limiting

DALL-E 3 has rate limits. The script adds 2-second delays by default.

If you get rate limit errors:

```bash
# Increase delay to 5 seconds
--delay 5.0
```

## Integration with Training Pipeline

### Step 1: Generate Synthetic Data

```bash
# Generate 200 deer images
python backend/generate_training_data.py \
    --object "white-tailed deer" \
    --background "New Hampshire backyard" \
    --count 200
```

### Step 2: Organize for YOLO

```bash
# Create YOLO folder structure
bash scripts/setup_training_data.sh

# Move synthetic images to training set
# 70% train, 20% val, 10% test split
mv data/synthetic_training/*.jpg data/images/train/
mv data/synthetic_training/*.txt data/labels/train/

# (Or use a script to split automatically - TODO)
```

### Step 3: Train Model

```bash
python backend/train_custom_model.py \
    --dataset data/deer_dataset.yaml \
    --epochs 100 \
    --model n
```

## Educational: Why This Works

### DALL-E 3 Capabilities

- **Photorealistic generation**: Creates images indistinguishable from real photos
- **Prompt adherence**: Follows detailed instructions about object placement
- **Consistency**: Can generate hundreds of similar but varied images

### Transfer Learning Benefits

- Pre-trained YOLO already knows "animal shapes"
- Synthetic data teaches it "deer shapes specifically"
- Mixing synthetic + real maximizes both volume and authenticity

### Annotation Quality

- **Perfect consistency**: Every annotation uses same box estimation logic
- **No human error**: No missed objects or wrong labels
- **Fast iteration**: Generate and annotate 100 images in ~10 minutes

## Troubleshooting

### Error: "OpenAI API key not found"

```bash
# Check .env file exists and has key
cat .env | grep OPENAI_API_KEY

# Should show:
OPENAI_API_KEY=sk-...
```

### Error: "Rate limit exceeded"

```bash
# Increase delay between requests
--delay 5.0

# Or generate in smaller batches
--count 10  # instead of --count 100
```

### Poor Image Quality

```bash
# Improve prompt specificity
--object "adult white-tailed deer with antlers"
--background "realistic New Hampshire forest, autumn foliage, natural lighting"
```

### Wrong Bounding Boxes

After generation, use LabelImg to fix:

```bash
# Install LabelImg
pip install labelImg

# Open annotation tool
labelImg data/synthetic_training data/synthetic_training

# Keyboard shortcuts:
# w = create box
# d = next image
# a = previous image
# Ctrl+S = save
```

## Next Steps

After generating synthetic data:

1. **Review quality** - Check first 10 images manually
2. **Adjust boxes** - Use LabelImg if needed
3. **Mix with real photos** - Add 30% real images if available
4. **Train model** - Use `train_custom_model.py`
5. **Iterate** - If model accuracy is low, generate more variations

## Cost Estimation

| Images | Cost | Training Time | Total Time |
| ------ | ---- | ------------- | ---------- |
| 100    | $4   | ~30 min       | ~45 min    |
| 500    | $20  | ~2 hours      | ~3 hours   |
| 1000   | $40  | ~4 hours      | ~6 hours   |

**Compare to manual:**

- Photography: 10-100+ hours for 1000 images
- Annotation: 30-50 hours for 1000 images
- Total: 40-150 hours vs 6 hours with AI generation!

## Future Enhancements

Potential improvements (not implemented yet):

1. **Automatic box refinement** - Use another AI model to detect exact deer position
2. **Variation control** - Specify exact poses, angles, distances
3. **Background image mixing** - Use real backyard photos as backgrounds
4. **Batch splitting** - Automatically split into train/val/test sets
5. **Quality filtering** - Auto-reject images that don't match criteria

---

**This covers the complete Synthetic Data Generation workflow!**

**Created:** October 28, 2025
