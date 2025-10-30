# Object Detection with Pre-trained YOLO
#
# This module handles animal/object detection using YOLOv8n pre-trained model.
#
# Educational Notes:
# - YOLOv8n is the "nano" version - smallest and fastest (6MB)
# - Pre-trained on COCO dataset (80 object classes)
# - Detects: person, dog, cat, bird, horse, bear, and 74 other classes
# - Returns bounding boxes, class names, and confidence scores
# - Runs on CPU (no GPU needed, though GPU would be faster)

import cv2
import time
from pathlib import Path
from ultralytics import YOLO
import logging

logger = logging.getLogger(__name__)

# COCO dataset classes that are relevant for yard tracking
YARD_ANIMALS = [
    'person', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe'
]

class YOLODetector:
    """Handles object detection using YOLO model"""
    
    def __init__(self, model_name='yolov8n.pt', confidence_threshold=0.5):
        """
        Initialize YOLO detector
        
        Args:
            model_name: Model to use ('yolov8n.pt' for nano, or full path like 'models/custom_model/weights/best.pt')
            confidence_threshold: Minimum confidence score to consider a detection (0.0-1.0)
        """
        self.confidence_threshold = confidence_threshold
        
        # Handle both simple names and full paths
        model_path = Path(model_name)
        if model_path.is_absolute() or str(model_name).startswith('models/'):
            # Already a full path or starts with models/
            self.model_path = model_path
        else:
            # Simple name like 'yolov8n.pt' - add models/ prefix
            self.model_path = Path('models') / model_name
        
        self.model = None
        
        logger.info(f"🤖 Initializing YOLO detector...")
        logger.info(f"📊 Confidence threshold: {confidence_threshold}")
        
        # Load model (will download if not exists)
        self._load_model()
    
    def _load_model(self):
        """Load or download YOLO model"""
        try:
            # Create models directory if it doesn't exist
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📦 Loading model: {self.model_path.name}")
            
            # This will download the model if it doesn't exist (~6MB for yolov8n)
            self.model = YOLO(str(self.model_path))
            
            # Get class names from model
            self.class_names = self.model.names
            
            logger.info(f"✅ Model loaded successfully")
            logger.info(f"📋 Model can detect {len(self.class_names)} object classes")
            logger.info(f"🐾 Yard-relevant classes: {', '.join(YARD_ANIMALS)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def detect(self, image_path, save_visualization=False):
        """
        Detect objects in an image
        
        Args:
            image_path: Path to image file
            save_visualization: If True, save image with bounding boxes drawn
        
        Returns:
            List of detections, each containing:
            {
                'class': 'dog',
                'confidence': 0.85,
                'bbox': [x1, y1, x2, y2]  # Coordinates of bounding box
            }
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            logger.error(f"❌ Image not found: {image_path}")
            return []
        
        try:
            # Run detection
            start_time = time.time()
            results = self.model.predict(
                source=str(image_path),
                conf=self.confidence_threshold,
                verbose=False  # Suppress detailed logging
            )
            inference_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Parse results
            detections = []
            result = results[0]  # First (and only) image
            
            # Get image dimensions for normalization
            img_height, img_width = result.orig_shape
            
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = self.class_names[class_id]
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                
                # Calculate normalized bbox for database
                x1, y1, x2, y2 = bbox
                bbox_norm = {
                    'x': (x1 + x2) / 2 / img_width,      # center x (normalized)
                    'y': (y1 + y2) / 2 / img_height,     # center y (normalized)
                    'width': (x2 - x1) / img_width,       # width (normalized)
                    'height': (y2 - y1) / img_height      # height (normalized)
                }
                
                detection = {
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': bbox,
                    'bbox_norm': bbox_norm
                }
                detections.append(detection)
            
            # Log results
            if detections:
                logger.info(f"🔍 Detected {len(detections)} object(s) in {image_path.name} ({inference_time:.0f}ms)")
                for det in detections:
                    logger.info(f"   🐾 {det['class']}: {det['confidence']:.2%} confidence")
            else:
                logger.debug(f"🔍 No objects detected in {image_path.name} ({inference_time:.0f}ms)")
            
            # Optionally save visualization
            if save_visualization and detections:
                self._save_visualization(image_path, detections)
            
            return detections
            
        except Exception as e:
            logger.error(f"❌ Detection failed for {image_path.name}: {e}")
            return []
    
    def _save_visualization(self, image_path, detections):
        """Draw bounding boxes on image and save"""
        try:
            # Read image
            image = cv2.imread(str(image_path))
            
            # Draw each detection
            for det in detections:
                x1, y1, x2, y2 = [int(coord) for coord in det['bbox']]
                class_name = det['class']
                confidence = det['confidence']
                
                # Draw rectangle
                color = (0, 255, 0)  # Green
                thickness = 2
                cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
                
                # Draw label with background
                label = f"{class_name} {confidence:.2%}"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                font_thickness = 2
                
                # Get text size for background
                (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
                
                # Draw background rectangle for text
                cv2.rectangle(image, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
                
                # Draw text
                cv2.putText(image, label, (x1, y1 - 5), font, font_scale, (0, 0, 0), font_thickness)
            
            # Save to detections subfolder
            output_dir = image_path.parent / 'detections'
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"detected_{image_path.name}"
            
            cv2.imwrite(str(output_path), image)
            logger.debug(f"💾 Saved visualization: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save visualization: {e}")
    
    def detect_batch(self, image_paths, save_visualization=False):
        """
        Detect objects in multiple images
        
        Args:
            image_paths: List of image file paths
            save_visualization: If True, save images with bounding boxes
        
        Returns:
            Dict mapping image_path to list of detections
        """
        results = {}
        total_detections = 0
        start_time = time.time()
        
        for image_path in image_paths:
            detections = self.detect(image_path, save_visualization)
            results[str(image_path)] = detections
            total_detections += len(detections)
        
        elapsed_time = time.time() - start_time
        logger.info(f"📊 Batch complete: {len(image_paths)} images, {total_detections} total detections in {elapsed_time:.1f}s")
        
        return results

def test_detector():
    """Test the detector on captured photos"""
    logger.info("=" * 60)
    logger.info("🧪 Testing YOLO Detector")
    logger.info("=" * 60)
    
    # Initialize detector
    detector = YOLODetector(confidence_threshold=0.3)  # Lower threshold for testing
    
    # Find recent photos
    photo_dir = Path('data/photos')
    photos = sorted(photo_dir.glob('yard_*.jpg'))[-5:]  # Last 5 photos
    
    if not photos:
        logger.warning("⚠️  No photos found to test. Run camera_capture.py first!")
        return
    
    logger.info(f"📸 Testing on {len(photos)} recent photos")
    logger.info("")
    
    # Test each photo
    for photo in photos:
        detections = detector.detect(photo, save_visualization=True)
        
        if not detections:
            logger.info(f"   (No objects detected above confidence threshold)")
        logger.info("")
    
    logger.info("=" * 60)
    logger.info("✅ Test complete!")
    logger.info(f"🖼️  Check data/photos/detections/ for visualizations")
    logger.info("=" * 60)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    test_detector()
