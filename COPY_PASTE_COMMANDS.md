# Copy-Paste Commands for Custom Model Training

Quick reference for copying commands directly into your terminal.

---

## Option 1: OpenAI DALL-E 3 (Synthetic Data) - ~$4 for 100 images

### Step 1: Set up API key
```bash
# Add to .env file:
OPENAI_API_KEY=sk-your-key-here
```

### Step 2: Generate synthetic images
```bash
python backend/training/generate_training_data.py --object "coffee mug" --background "kitchen countertop with natural lighting" --count 100
```

### Step 3: Prepare dataset
```bash
python backend/training/prepare_dataset.py --input data/synthetic_training --output data/training_data --split 70 20 10 --clean
```

### Step 4: Train model
```bash
python backend/training/train_custom_model.py --dataset data/coffee_mug_dataset.yaml --epochs 100 --batch 8 --model n
```

### Step 5: Test model
```bash
python backend/training/test_custom_model.py --model models/custom_model/weights/best.pt --images data/training_data/images/val --confidence 0.25
```

---

## Option 2: Pexels Stock Photos (FREE) - Recommended

### Step 1: Set up API key (FREE from pexels.com/api)
```bash
# Add to .env file:
PEXELS_API_KEY=your-key-here
```

### Step 2: Fetch images from Pexels
```bash
python backend/training/fetch_images.py --query "coffee mug" --count 30 --source pexels
```

### Step 3: Auto-annotate with YOLOv8n
```bash
python backend/training/auto_annotate.py --input data/to_annotate --output data/to_annotate --model models/yolov8n.pt --class-ids 0
```

### Step 4: Manual review in GUI
```bash
python backend/training/annotation_tool.py --input data/to_annotate --class-ids 0
```

**In the GUI:**
- Click and drag to create bounding boxes
- Use arrow keys to navigate images
- Press S to save, Del to delete box
- Click "Add to Training Set" when done

### Step 5: Prepare dataset
```bash
python backend/training/prepare_dataset.py --input data/synthetic_training --output data/training_data --split 70 20 10 --clean
```

### Step 6: Train model
```bash
python backend/training/train_custom_model.py --dataset data/coffee_mug_dataset.yaml --epochs 100 --batch 8 --model n
```

### Step 7: Test model
```bash
python backend/training/test_custom_model.py --model models/custom_model/weights/best.pt --images data/training_data/images/val --confidence 0.25
```

---

## Rapid Iteration Loop (Pexels Method)

### Fetch more images with different queries
```bash
python backend/training/fetch_images.py --query "white ceramic mug" --count 20 --source pexels
python backend/training/fetch_images.py --query "coffee cup on desk" --count 20 --source pexels
python backend/training/fetch_images.py --query "mug isolated white background" --count 20 --source pexels
```

### Auto-annotate only unannotated images
```bash
python backend/training/auto_annotate.py --input data/to_annotate --output data/to_annotate --model models/yolov8n.pt --class-ids 0
```

### Review only unannotated images
```bash
python backend/training/annotation_tool.py --input data/to_annotate --class-ids 0 --unannotated-only
```

### Add to training set, retrain, and test
```bash
# Click "Add to Training Set" in GUI, then:
python backend/training/prepare_dataset.py --input data/synthetic_training --output data/training_data --split 70 20 10 --clean
python backend/training/train_custom_model.py --dataset data/coffee_mug_dataset.yaml --epochs 100 --batch 8 --model n
python backend/training/test_custom_model.py --model models/custom_model/weights/best.pt --images data/training_data/images/val --confidence 0.04
```

---

## Common Variations

### Change object type
```bash
# For different object (e.g., "deer")
python backend/training/fetch_images.py --query "white-tailed deer" --count 30 --source pexels
python backend/training/auto_annotate.py --input data/to_annotate --output data/to_annotate --model models/yolov8n.pt --class-ids 0
python backend/training/annotation_tool.py --input data/to_annotate --class-ids 0 --classes "deer"
```

### Test with lower confidence threshold
```bash
python backend/training/test_custom_model.py --model models/custom_model/weights/best.pt --images data/training_data/images/val --confidence 0.01
```

### Visualize existing annotations
```bash
python backend/training/visualize_annotations.py --input data/synthetic_training --output data/annotation_check
```

### Clean up and start over
```bash
python backend/training/cleanup_dataset.py --all
```

---

## Pro Tips

- **Target 100-500+ images** for good model performance
- **Use varied queries** to get diverse training data
- **Lower confidence (0.01-0.10)** may work better for custom models
- **Mix synthetic + real images** for best results
- **Check `models/custom_model/results.png`** to see training progress charts
