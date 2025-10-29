#!/usr/bin/env python3
"""
Test Custom Model

Tests your trained model on new images to verify it works.

Usage:
    python backend/test_custom_model.py --model models/custom_model/weights/best.pt --images data/test_images/
"""

import argparse
from pathlib import Path
from ultralytics import YOLO
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_model(model_path, images_path, confidence=0.5):
    """Test custom model on images"""
    
    model_path = Path(model_path)
    images_path = Path(images_path)
    
    if not model_path.exists():
        logger.error(f"❌ Model not found: {model_path}")
        return
    
    if not images_path.exists():
        logger.error(f"❌ Images path not found: {images_path}")
        return
    
    # Load custom model
    logger.info(f"📦 Loading model: {model_path}")
    model = YOLO(str(model_path))
    
    # Get class names
    class_names = model.names
    logger.info(f"🏷️  Classes: {class_names}")
    
    # Find test images
    if images_path.is_file():
        test_images = [images_path]
    else:
        test_images = list(images_path.glob('*.jpg')) + list(images_path.glob('*.png'))
    
    logger.info(f"📸 Testing on {len(test_images)} images")
    logger.info(f"📊 Confidence threshold: {confidence}")
    logger.info("")
    
    # Test each image
    total_detections = 0
    images_with_detections = 0
    
    for img_path in test_images:
        logger.info(f"Testing: {img_path.name}")
        
        # Run prediction
        results = model.predict(
            source=str(img_path),
            conf=confidence,
            save=True,  # Save visualization
            project='models/custom_model',
            name='test_results',
            exist_ok=True
        )
        
        # Parse results
        result = results[0]
        detections = []
        
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = class_names[class_id]
            conf = float(box.conf[0])
            bbox = box.xyxy[0].tolist()
            
            detections.append({
                'class': class_name,
                'confidence': conf,
                'bbox': bbox
            })
        
        if detections:
            images_with_detections += 1
            total_detections += len(detections)
            logger.info(f"   ✅ Found {len(detections)} object(s):")
            for det in detections:
                logger.info(f"      🐾 {det['class']}: {det['confidence']:.2%}")
        else:
            logger.info(f"   ⚪ No detections")
        logger.info("")
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 Test Results Summary")
    logger.info("=" * 60)
    logger.info(f"Total images tested: {len(test_images)}")
    logger.info(f"Images with detections: {images_with_detections}")
    logger.info(f"Total detections: {total_detections}")
    logger.info(f"Detection rate: {images_with_detections/len(test_images)*100:.1f}%")
    logger.info("")
    logger.info(f"📁 Visualizations saved to: models/custom_model/test_results/")

def main():
    parser = argparse.ArgumentParser(description='Test custom YOLO model')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to trained model (.pt file)')
    parser.add_argument('--images', type=str, required=True,
                       help='Path to test images (file or directory)')
    parser.add_argument('--confidence', type=float, default=0.5,
                       help='Confidence threshold (default: 0.5)')
    
    args = parser.parse_args()
    
    test_model(args.model, args.images, args.confidence)

if __name__ == "__main__":
    main()
