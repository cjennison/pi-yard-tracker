#!/usr/bin/env python3
"""
Visualize YOLO Annotations

Draws bounding boxes on images using their YOLO annotation files.
This helps verify that annotations are correct before training.

Usage:
    python backend/visualize_annotations.py --input data/synthetic_training --output data/annotation_check
"""

import argparse
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnnotationVisualizer:
    """Visualizes YOLO annotations by drawing boxes on images"""
    
    def __init__(self, class_names=None):
        """
        Initialize visualizer
        
        Args:
            class_names: Dict mapping class IDs to names (e.g., {0: 'deer', 1: 'turkey'})
        """
        self.class_names = class_names or {0: 'object'}
        
        # Colors for different classes (BGR format for OpenCV compatibility)
        self.colors = [
            (0, 255, 0),    # Green for class 0
            (255, 0, 0),    # Blue for class 1
            (0, 0, 255),    # Red for class 2
            (255, 255, 0),  # Cyan for class 3
            (255, 0, 255),  # Magenta for class 4
        ]
    
    def parse_yolo_annotation(self, annotation_path):
        """
        Parse YOLO format annotation file
        
        YOLO format: class_id x_center y_center width height (all normalized 0-1)
        
        Args:
            annotation_path: Path to .txt annotation file
        
        Returns:
            List of tuples: [(class_id, x_center, y_center, width, height), ...]
        """
        annotations = []
        
        try:
            with open(annotation_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    
                    annotations.append((class_id, x_center, y_center, width, height))
            
            return annotations
            
        except Exception as e:
            logger.error(f"Failed to parse {annotation_path}: {e}")
            return []
    
    def draw_box(self, draw, x1, y1, x2, y2, class_id, class_name, color, width=3):
        """
        Draw a bounding box with label
        
        Args:
            draw: PIL ImageDraw object
            x1, y1, x2, y2: Box coordinates in pixels
            class_id: Class ID
            class_name: Class name string
            color: RGB color tuple
            width: Box line width
        """
        # Draw rectangle
        for i in range(width):
            draw.rectangle(
                [x1 + i, y1 + i, x2 - i, y2 - i],
                outline=color
            )
        
        # Draw label background
        label = f"{class_name} (ID:{class_id})"
        
        # Try to use a font, fall back to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Draw label background
        label_y = y1 - text_height - 4 if y1 - text_height - 4 > 0 else y1
        draw.rectangle(
            [x1, label_y, x1 + text_width + 4, label_y + text_height + 4],
            fill=color
        )
        
        # Draw label text
        draw.text(
            (x1 + 2, label_y + 2),
            label,
            fill=(255, 255, 255),
            font=font
        )
    
    def visualize_image(self, image_path, annotation_path, output_path):
        """
        Draw annotations on a single image
        
        Args:
            image_path: Path to image file
            annotation_path: Path to annotation .txt file
            output_path: Where to save annotated image
        
        Returns:
            Number of boxes drawn
        """
        try:
            # Load image
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            img_width, img_height = image.size
            
            # Parse annotations
            annotations = self.parse_yolo_annotation(annotation_path)
            
            if not annotations:
                logger.warning(f"No annotations found in {annotation_path.name}")
                return 0
            
            # Draw each box
            for class_id, x_center, y_center, width, height in annotations:
                # Convert normalized coordinates to pixels
                x_center_px = x_center * img_width
                y_center_px = y_center * img_height
                width_px = width * img_width
                height_px = height * img_height
                
                # Calculate box corners
                x1 = int(x_center_px - width_px / 2)
                y1 = int(y_center_px - height_px / 2)
                x2 = int(x_center_px + width_px / 2)
                y2 = int(y_center_px + height_px / 2)
                
                # Get class name and color
                class_name = self.class_names.get(class_id, f"class_{class_id}")
                color = self.colors[class_id % len(self.colors)]
                
                # Draw box
                self.draw_box(draw, x1, y1, x2, y2, class_id, class_name, color)
                
                logger.info(f"   📦 Drew box for '{class_name}' at ({x1}, {y1}) -> ({x2}, {y2})")
            
            # Save annotated image
            image.save(output_path, "JPEG", quality=95)
            
            return len(annotations)
            
        except Exception as e:
            logger.error(f"Failed to visualize {image_path}: {e}")
            return 0
    
    def visualize_directory(self, input_dir, output_dir):
        """
        Visualize all images in a directory
        
        Args:
            input_dir: Directory containing images and .txt annotations
            output_dir: Directory to save visualized images
        
        Returns:
            Total number of images processed
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(input_dir.glob(f'*{ext}'))
        
        if not image_files:
            logger.error(f"No images found in {input_dir}")
            return 0
        
        logger.info("=" * 60)
        logger.info(f"🎨 Visualizing Annotations")
        logger.info("=" * 60)
        logger.info(f"📂 Input: {input_dir}")
        logger.info(f"💾 Output: {output_dir}")
        logger.info(f"📸 Found {len(image_files)} images")
        logger.info("")
        
        processed = 0
        total_boxes = 0
        
        for image_path in sorted(image_files):
            # Find corresponding annotation file
            annotation_path = image_path.with_suffix('.txt')
            
            if not annotation_path.exists():
                logger.warning(f"⚠️  No annotation for {image_path.name}, skipping")
                continue
            
            logger.info(f"[{processed + 1}/{len(image_files)}] Processing {image_path.name}...")
            
            # Create output path
            output_path = output_dir / f"annotated_{image_path.name}"
            
            # Visualize
            num_boxes = self.visualize_image(image_path, annotation_path, output_path)
            
            if num_boxes > 0:
                processed += 1
                total_boxes += num_boxes
                logger.info(f"   ✅ Saved to {output_path.name}")
            
            logger.info("")
        
        logger.info("=" * 60)
        logger.info(f"✅ Complete!")
        logger.info(f"📊 Processed: {processed} images")
        logger.info(f"📦 Total boxes: {total_boxes}")
        logger.info(f"💾 Output: {output_dir}")
        logger.info("=" * 60)
        
        return processed

def main():
    parser = argparse.ArgumentParser(
        description='Visualize YOLO annotations by drawing boxes on images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize all images in synthetic_training folder
  python backend/visualize_annotations.py \\
      --input data/synthetic_training \\
      --output data/annotation_check

  # Visualize training dataset
  python backend/visualize_annotations.py \\
      --input data/training_data/images/train \\
      --output data/annotation_check/train

  # Custom class names
  python backend/visualize_annotations.py \\
      --input data/synthetic_training \\
      --output data/annotation_check \\
      --classes deer turkey rabbit
        """
    )
    
    parser.add_argument('--input', type=str, required=True,
                       help='Input directory with images and .txt annotations')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory for annotated images')
    parser.add_argument('--classes', nargs='+', default=['deer'],
                       help='Class names in order (default: deer)')
    
    args = parser.parse_args()
    
    # Create class name mapping
    class_names = {i: name for i, name in enumerate(args.classes)}
    
    # Visualize
    visualizer = AnnotationVisualizer(class_names=class_names)
    visualizer.visualize_directory(args.input, args.output)

if __name__ == "__main__":
    main()
