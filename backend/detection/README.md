# Detection Module

YOLO-based object detection for wildlife tracking.

## Scripts

### `detector.py`

Run object detection on images using YOLO models.

**Usage:**

```bash
# With pre-trained model
python backend/detection/detector.py --model models/yolov8n.pt --source data/photos/

# With custom model
python backend/detection/detector.py --model models/custom_model/weights/best.pt --source data/photos/
```

**Features:**

- YOLOv8 integration
- Animal filtering (COCO classes 15-24)
- Bounding box visualization
- Confidence thresholding
- Batch processing

**Dependencies:**

- ultralytics
- opencv-python
- pillow

## Class: YOLODetector

Main detection class with methods:

- `detect_objects()`: Run inference on image
- `filter_animals()`: Filter for animal classes
- `save_detections()`: Save annotated images
