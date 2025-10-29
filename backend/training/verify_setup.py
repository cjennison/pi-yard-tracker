"""
Verification Script - Diagnose Training Setup

This script checks if our training setup is correct by:
1. Loading base YOLOv8n model
2. Testing on our training images
3. Verifying annotations match images
4. Checking if model architecture is correct
"""

import logging
from pathlib import Path
from ultralytics import YOLO
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_base_model():
    """Test that base YOLOv8n model works on our images"""
    logger.info("=" * 60)
    logger.info("1. Testing Base YOLOv8n Model")
    logger.info("=" * 60)
    
    try:
        model = YOLO('models/yolov8n.pt')
        logger.info("✅ Base model loaded successfully")
        
        # Test on one training image
        test_image = Path('data/training_data/images/train')
        image_files = list(test_image.glob('*.jpg')) + list(test_image.glob('*.png'))
        
        if image_files:
            test_img = image_files[0]
            logger.info(f"📸 Testing on: {test_img.name}")
            
            results = model(str(test_img), conf=0.25)
            
            if results and len(results) > 0:
                detections = results[0].boxes
                logger.info(f"✅ Model ran successfully")
                logger.info(f"   Detections: {len(detections)}")
                
                for box in detections:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    cls_name = model.names[cls_id]
                    logger.info(f"   - {cls_name}: {conf:.2%}")
            else:
                logger.warning("⚠️  No detections (normal if mug not in COCO classes)")
        else:
            logger.error("❌ No training images found!")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Base model test failed: {e}")
        return False

def verify_annotations():
    """Check that annotations are correctly formatted"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("2. Verifying Annotation Format")
    logger.info("=" * 60)
    
    train_labels = Path('data/training_data/labels/train')
    train_images = Path('data/training_data/images/train')
    
    label_files = list(train_labels.glob('*.txt'))
    logger.info(f"📝 Found {len(label_files)} annotation files")
    
    issues = []
    
    for label_file in label_files[:5]:  # Check first 5
        try:
            with open(label_file, 'r') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                parts = line.strip().split()
                
                if len(parts) != 5:
                    issues.append(f"{label_file.name} line {line_num}: Expected 5 values, got {len(parts)}")
                    continue
                
                try:
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    
                    # Check class ID
                    if class_id != 0:
                        issues.append(f"{label_file.name} line {line_num}: class_id={class_id} (should be 0)")
                    
                    # Check normalized coordinates
                    if not (0 <= x_center <= 1 and 0 <= y_center <= 1 and 0 <= width <= 1 and 0 <= height <= 1):
                        issues.append(f"{label_file.name} line {line_num}: Coordinates not normalized (0-1)")
                    
                    logger.info(f"✅ {label_file.name}: class={class_id}, bbox=({x_center:.2f}, {y_center:.2f}, {width:.2f}, {height:.2f})")
                    
                except ValueError as e:
                    issues.append(f"{label_file.name} line {line_num}: Invalid number format - {e}")
            
            # Check matching image exists
            image_extensions = ['.jpg', '.png', '.jpeg', '.webp']
            image_found = False
            for ext in image_extensions:
                image_path = train_images / f"{label_file.stem}{ext}"
                if image_path.exists():
                    image_found = True
                    break
            
            if not image_found:
                issues.append(f"{label_file.name}: No matching image found")
                
        except Exception as e:
            issues.append(f"{label_file.name}: Error reading file - {e}")
    
    if issues:
        logger.error(f"❌ Found {len(issues)} annotation issues:")
        for issue in issues:
            logger.error(f"   - {issue}")
        return False
    else:
        logger.info(f"✅ All checked annotations are valid!")
        return True

def verify_dataset_config():
    """Check dataset YAML configuration"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("3. Verifying Dataset Configuration")
    logger.info("=" * 60)
    
    import yaml
    
    config_path = Path('data/coffee_mug_dataset.yaml')
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        logger.info(f"✅ YAML loaded successfully")
        logger.info(f"   nc (num classes): {config.get('nc', 'NOT SET')}")
        logger.info(f"   names: {config.get('names', 'NOT SET')}")
        logger.info(f"   path: {config.get('path', 'NOT SET')}")
        logger.info(f"   train: {config.get('train', 'NOT SET')}")
        logger.info(f"   val: {config.get('val', 'NOT SET')}")
        
        # Verify paths exist
        base_path = Path(config['path'])
        train_path = base_path / config['train']
        val_path = base_path / config['val']
        
        if not base_path.exists():
            logger.error(f"❌ Base path doesn't exist: {base_path}")
            return False
        
        if not train_path.exists():
            logger.error(f"❌ Train path doesn't exist: {train_path}")
            return False
        
        if not val_path.exists():
            logger.error(f"❌ Val path doesn't exist: {val_path}")
            return False
        
        logger.info(f"✅ All paths exist")
        
        # Check class count
        if config['nc'] != 1:
            logger.error(f"❌ nc should be 1 for single-class, got {config['nc']}")
            return False
        
        if 0 not in config['names'] or config['names'][0] != 'coffee_mug':
            logger.error(f"❌ names[0] should be 'coffee_mug'")
            return False
        
        logger.info(f"✅ Configuration is correct!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load dataset config: {e}")
        return False

def check_image_label_pairs():
    """Verify every image has a matching label"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("4. Checking Image-Label Pairs")
    logger.info("=" * 60)
    
    train_images = Path('data/training_data/images/train')
    train_labels = Path('data/training_data/labels/train')
    
    image_files = list(train_images.glob('*.jpg')) + list(train_images.glob('*.png')) + list(train_images.glob('*.webp'))
    label_files = list(train_labels.glob('*.txt'))
    
    logger.info(f"📸 Images: {len(image_files)}")
    logger.info(f"📝 Labels: {len(label_files)}")
    
    missing_labels = []
    for img in image_files:
        label_path = train_labels / f"{img.stem}.txt"
        if not label_path.exists():
            missing_labels.append(img.name)
    
    missing_images = []
    for label in label_files:
        found = False
        for ext in ['.jpg', '.png', '.jpeg', '.webp']:
            img_path = train_images / f"{label.stem}{ext}"
            if img_path.exists():
                found = True
                break
        if not found:
            missing_images.append(label.name)
    
    if missing_labels:
        logger.error(f"❌ {len(missing_labels)} images missing labels:")
        for name in missing_labels[:5]:
            logger.error(f"   - {name}")
        return False
    
    if missing_images:
        logger.error(f"❌ {len(missing_images)} labels missing images:")
        for name in missing_images[:5]:
            logger.error(f"   - {name}")
        return False
    
    logger.info(f"✅ All image-label pairs match!")
    return True

def main():
    """Run all verification checks"""
    logger.info("🔍 Training Setup Verification")
    logger.info("")
    
    checks = [
        ("Base Model", verify_base_model),
        ("Annotations", verify_annotations),
        ("Dataset Config", verify_dataset_config),
        ("Image-Label Pairs", check_image_label_pairs),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            logger.error(f"❌ {name} check crashed: {e}")
            results[name] = False
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("🎉 All checks passed! Training setup is correct.")
        logger.info("")
        logger.info("📊 The issue is likely insufficient training data (30 images).")
        logger.info("   Recommendation: Add 100-500+ images for good results.")
    else:
        logger.error("⚠️  Some checks failed. Fix issues before training.")
    
    logger.info("")

if __name__ == "__main__":
    main()
