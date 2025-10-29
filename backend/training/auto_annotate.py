"""
Auto-Annotate Images using Pre-trained YOLO Model

This script automatically generates YOLO format annotations for images
in the data/to_annotate folder using the pre-trained YOLOv8n model.
Users can then manually correct these annotations using annotation_tool.py.
"""

import argparse
import logging
from pathlib import Path
from typing import List, Tuple
from ultralytics import YOLO
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AutoAnnotator:
    """Automatically annotate images using pre-trained YOLO model"""
    
    def __init__(self, model_path: Path, confidence: float = 0.3):
        """
        Initialize auto-annotator
        
        Args:
            model_path: Path to YOLO model (.pt file)
            confidence: Minimum confidence threshold for detections
        """
        self.model_path = Path(model_path)
        self.confidence = confidence
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            logger.info(f"📦 Loading model: {self.model_path}")
            self.model = YOLO(str(self.model_path))
            logger.info(f"✅ Model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def find_images(self, input_dir: Path) -> List[Path]:
        """
        Find all images in directory
        
        Args:
            input_dir: Directory to search
            
        Returns:
            List of image paths
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        images = []
        
        for ext in image_extensions:
            images.extend(input_dir.glob(f'*{ext}'))
            images.extend(input_dir.glob(f'*{ext.upper()}'))
        
        return sorted(images)
    
    def annotate_image(self, image_path: Path) -> Tuple[int, Path]:
        """
        Generate YOLO annotation for single image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (num_detections, annotation_path)
        """
        # Check if annotation already exists
        annotation_path = image_path.with_suffix('.txt')
        if annotation_path.exists():
            logger.info(f"⏭️  Skipping {image_path.name} (annotation already exists)")
            return (0, annotation_path)
        
        # Run detection
        try:
            results = self.model(str(image_path), conf=self.confidence, verbose=False)
        except Exception as e:
            logger.error(f"❌ Detection failed for {image_path.name}: {e}")
            return (0, annotation_path)
        
        # Get image dimensions
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # Extract detections and convert to YOLO format
        annotations = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get box coordinates (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                # Convert to YOLO format (normalized x_center, y_center, width, height)
                x_center = ((x1 + x2) / 2) / img_width
                y_center = ((y1 + y2) / 2) / img_height
                width = (x2 - x1) / img_width
                height = (y2 - y1) / img_height
                
                # Get class ID and confidence
                class_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Format: class_id x_center y_center width height
                annotation = f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
                annotations.append(annotation)
                
                class_name = self.model.names[class_id]
                logger.info(f"   📍 Detected {class_name} (class {class_id}) at {conf:.2%} confidence")
        
        # Save annotations to file
        if annotations:
            with open(annotation_path, 'w') as f:
                f.write('\n'.join(annotations))
            logger.info(f"✅ Saved {len(annotations)} annotation(s) to {annotation_path.name}")
        else:
            logger.warning(f"⚠️  No objects detected in {image_path.name}")
            # Create empty annotation file
            annotation_path.touch()
        
        return (len(annotations), annotation_path)
    
    def annotate_directory(self, input_dir: Path, skip_existing: bool = True) -> dict:
        """
        Auto-annotate all images in directory
        
        Args:
            input_dir: Directory containing images
            skip_existing: Skip images that already have annotations
            
        Returns:
            Dictionary with statistics
        """
        input_dir = Path(input_dir)
        
        if not input_dir.exists():
            logger.error(f"❌ Directory not found: {input_dir}")
            return {}
        
        # Find all images
        images = self.find_images(input_dir)
        
        if not images:
            logger.warning(f"⚠️  No images found in {input_dir}")
            return {}
        
        logger.info(f"📸 Found {len(images)} image(s) in {input_dir}")
        logger.info(f"🎯 Confidence threshold: {self.confidence}")
        logger.info("")
        
        # Process each image
        total_detections = 0
        annotated_count = 0
        skipped_count = 0
        
        for i, image_path in enumerate(images, 1):
            logger.info(f"[{i}/{len(images)}] Processing: {image_path.name}")
            
            num_detections, annotation_path = self.annotate_image(image_path)
            
            if annotation_path.exists() and annotation_path.stat().st_size > 0:
                if num_detections > 0:
                    total_detections += num_detections
                    annotated_count += 1
                else:
                    skipped_count += 1
            
            logger.info("")
        
        # Summary
        stats = {
            'total_images': len(images),
            'annotated': annotated_count,
            'skipped': skipped_count,
            'total_detections': total_detections
        }
        
        logger.info("=" * 60)
        logger.info("📊 Auto-Annotation Summary")
        logger.info("=" * 60)
        logger.info(f"Total images: {stats['total_images']}")
        logger.info(f"Newly annotated: {stats['annotated']}")
        logger.info(f"Skipped (already annotated): {stats['skipped']}")
        logger.info(f"Total detections: {stats['total_detections']}")
        logger.info("")
        logger.info("✅ Next step: Run 'python backend/training/annotation_tool.py' to review/correct annotations")
        
        return stats


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Auto-annotate images using pre-trained YOLO model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-annotate all images in to_annotate folder
  python backend/training/auto_annotate.py
  
  # Use custom confidence threshold
  python backend/training/auto_annotate.py --confidence 0.5
  
  # Use custom model
  python backend/training/auto_annotate.py --model models/custom_model/weights/best.pt
  
  # Specify input directory
  python backend/training/auto_annotate.py --input data/my_images
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        default='data/to_annotate',
        help='Input directory containing images (default: data/to_annotate)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='models/yolov8n.pt',
        help='Path to YOLO model (default: models/yolov8n.pt)'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.3,
        help='Minimum confidence threshold (default: 0.3)'
    )
    
    args = parser.parse_args()
    
    # Create annotator
    annotator = AutoAnnotator(
        model_path=args.model,
        confidence=args.confidence
    )
    
    # Run auto-annotation
    annotator.annotate_directory(args.input)


if __name__ == "__main__":
    main()
