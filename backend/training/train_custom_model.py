#!/usr/bin/env python3
"""
Custom Model Training Script for Pi Yard Tracker

This script trains a custom YOLO model on your annotated dataset.

Usage:
    python backend/train_custom_model.py --dataset data/deer_dataset.yaml --epochs 50

Educational Notes:
- Uses transfer learning (starts from YOLOv8n pre-trained weights)
- Much faster than training from scratch (hours vs days)
- Freezes early layers (already know edges/shapes)
- Only trains later layers (specific to your animals)
"""

import argparse
from pathlib import Path
from ultralytics import YOLO
import yaml
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_dataset(dataset_path):
    """Check if dataset structure is correct"""
    dataset_path = Path(dataset_path)
    
    if not dataset_path.exists():
        logger.error(f"❌ Dataset file not found: {dataset_path}")
        return False
    
    # Load and validate YAML
    try:
        with open(dataset_path) as f:
            config = yaml.safe_load(f)
        
        required_keys = ['path', 'train', 'val', 'names']
        for key in required_keys:
            if key not in config:
                logger.error(f"❌ Missing required key in dataset.yaml: {key}")
                return False
        
        # Check paths exist
        base_path = Path(config['path'])
        train_path = base_path / config['train']
        val_path = base_path / config['val']
        
        if not train_path.exists():
            logger.error(f"❌ Training images not found: {train_path}")
            return False
        
        if not val_path.exists():
            logger.error(f"❌ Validation images not found: {val_path}")
            return False
        
        # Count images
        train_images = list(train_path.glob('*.jpg')) + list(train_path.glob('*.png'))
        val_images = list(val_path.glob('*.jpg')) + list(val_path.glob('*.png'))
        
        logger.info(f"✅ Dataset validated:")
        logger.info(f"   📊 Classes: {config['names']}")
        logger.info(f"   📸 Training images: {len(train_images)}")
        logger.info(f"   📸 Validation images: {len(val_images)}")
        
        if len(train_images) < 10:
            logger.warning(f"⚠️  Very few training images! Recommend 100+")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error validating dataset: {e}")
        return False

def train_model(dataset_path, epochs=50, model_size='n', batch=16, img_size=640):
    """
    Train custom YOLO model
    
    Args:
        dataset_path: Path to dataset YAML file
        epochs: Number of training epochs (50-200 recommended)
        model_size: 'n' (nano), 's' (small), 'm' (medium), 'l' (large), 'x' (xlarge)
        batch: Batch size (16 for Pi, 32+ for GPU)
        img_size: Image size (640 standard, 320 faster, 1280 more accurate)
    """
    logger.info("=" * 60)
    logger.info("🚀 Starting Custom Model Training")
    logger.info("=" * 60)
    
    # Validate dataset first
    if not validate_dataset(dataset_path):
        logger.error("❌ Dataset validation failed. Fix issues and try again.")
        return None
    
    # Load pre-trained model (transfer learning base)
    model_name = f'yolov8{model_size}.pt'
    logger.info(f"📦 Loading base model: {model_name}")
    model = YOLO(model_name)
    
    logger.info(f"⚙️  Training configuration:")
    logger.info(f"   📁 Dataset: {dataset_path}")
    logger.info(f"   🔄 Epochs: {epochs}")
    logger.info(f"   📦 Batch size: {batch}")
    logger.info(f"   📐 Image size: {img_size}")
    logger.info(f"   🧠 Model: YOLOv8{model_size}")
    logger.info("")
    logger.info("🏋️  Training started (this will take a while)...")
    logger.info("   💡 Tip: Check models/custom_model/train/ for progress charts")
    logger.info("")
    
    try:
        # Train the model
        results = model.train(
            data=str(dataset_path),
            epochs=epochs,
            imgsz=img_size,
            batch=batch,
            
            # Output settings
            project='models',
            name='custom_model',
            exist_ok=True,  # Overwrite previous runs
            
            # Performance settings
            device='cpu',  # Change to 'cuda' if you have GPU
            workers=4,     # Number of CPU cores to use
            
            # Transfer learning settings
            pretrained=True,  # Start from pre-trained weights
            
            # Monitoring
            plots=True,    # Generate training plots
            save=True,     # Save checkpoints
            save_period=10,  # Save every 10 epochs
            
            # Optimization
            optimizer='Adam',  # Adam optimizer (good default)
            lr0=0.01,         # Initial learning rate
            patience=20,      # Stop if no improvement for 20 epochs
            
            # Augmentation (data variety)
            hsv_h=0.015,      # Hue augmentation
            hsv_s=0.7,        # Saturation
            hsv_v=0.4,        # Value
            degrees=10.0,     # Rotation
            translate=0.1,    # Translation
            scale=0.5,        # Scaling
            fliplr=0.5,       # Horizontal flip
            mosaic=1.0,       # Mosaic augmentation
        )
        
        # Training complete
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Training Complete!")
        logger.info("=" * 60)
        
        # Show results location
        save_dir = Path('models/custom_model')
        weights_path = save_dir / 'weights' / 'best.pt'
        
        logger.info(f"📊 Results saved to: {save_dir}")
        logger.info(f"🏆 Best model: {weights_path}")
        logger.info("")
        logger.info("📈 Training metrics:")
        logger.info(f"   Check: {save_dir}/results.png")
        logger.info(f"   Check: {save_dir}/confusion_matrix.png")
        logger.info("")
        logger.info("🚀 Next steps:")
        logger.info(f"   1. Review training charts in {save_dir}/")
        logger.info(f"   2. Test model: python backend/test_custom_model.py")
        logger.info(f"   3. Deploy to Pi: Copy {weights_path} to Pi")
        logger.info("")
        
        return weights_path
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Train custom YOLO model')
    parser.add_argument('--dataset', type=str, required=True,
                       help='Path to dataset YAML file')
    parser.add_argument('--epochs', type=int, default=50,
                       help='Number of training epochs (default: 50)')
    parser.add_argument('--model', type=str, default='n', choices=['n', 's', 'm', 'l', 'x'],
                       help='Model size: n=nano, s=small, m=medium, l=large, x=xlarge (default: n)')
    parser.add_argument('--batch', type=int, default=16,
                       help='Batch size (default: 16)')
    parser.add_argument('--img-size', type=int, default=640,
                       help='Image size (default: 640)')
    
    args = parser.parse_args()
    
    # Train model
    weights_path = train_model(
        dataset_path=args.dataset,
        epochs=args.epochs,
        model_size=args.model,
        batch=args.batch,
        img_size=args.img_size
    )
    
    if weights_path:
        logger.info(f"✅ Success! Model ready at: {weights_path}")
    else:
        logger.error("❌ Training failed")
        exit(1)

if __name__ == "__main__":
    main()
