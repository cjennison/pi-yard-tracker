#!/usr/bin/env python3
"""
Dataset Preparation Script

Organizes synthetic training data into YOLO format with train/val/test splits.

Usage:
    python backend/prepare_dataset.py --input data/synthetic_training --output data/training_data --split 70 20 10
"""

import argparse
import shutil
import random
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatasetPreparer:
    """Prepares YOLO dataset from synthetic training images"""
    
    def __init__(self, input_dir, output_dir, train_split=0.7, val_split=0.2, test_split=0.1):
        """
        Initialize dataset preparer
        
        Args:
            input_dir: Directory containing synthetic images and labels
            output_dir: Directory to create YOLO dataset structure
            train_split: Fraction for training (0-1)
            val_split: Fraction for validation (0-1)
            test_split: Fraction for testing (0-1)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Normalize splits to sum to 1.0
        total = train_split + val_split + test_split
        self.train_split = train_split / total
        self.val_split = val_split / total
        self.test_split = test_split / total
        
        logger.info(f"📊 Split ratios: train={self.train_split:.1%}, val={self.val_split:.1%}, test={self.test_split:.1%}")
    
    def create_directory_structure(self):
        """Create YOLO dataset directory structure"""
        logger.info("📁 Creating directory structure...")
        
        # Create main directories
        for split in ['train', 'val', 'test']:
            (self.output_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
            (self.output_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Created structure in {self.output_dir}")
    
    def find_image_label_pairs(self):
        """
        Find all image-label pairs in input directory
        
        Returns:
            List of (image_path, label_path) tuples
        """
        logger.info(f"🔍 Scanning {self.input_dir} for images...")
        
        pairs = []
        
        # Look for all image files
        for img_ext in ['*.jpg', '*.jpeg', '*.png']:
            for image_path in self.input_dir.glob(img_ext):
                # Check if corresponding .txt label exists
                label_path = image_path.with_suffix('.txt')
                
                if label_path.exists():
                    pairs.append((image_path, label_path))
                else:
                    logger.warning(f"⚠️  No label found for {image_path.name}")
        
        logger.info(f"✅ Found {len(pairs)} image-label pairs")
        return pairs
    
    def split_dataset(self, pairs):
        """
        Split pairs into train/val/test sets
        
        Args:
            pairs: List of (image_path, label_path) tuples
        
        Returns:
            Dict with 'train', 'val', 'test' keys containing lists of pairs
        """
        logger.info("🎲 Shuffling and splitting dataset...")
        
        # Shuffle pairs for random split
        random.shuffle(pairs)
        
        n_total = len(pairs)
        n_train = int(n_total * self.train_split)
        n_val = int(n_total * self.val_split)
        
        splits = {
            'train': pairs[:n_train],
            'val': pairs[n_train:n_train + n_val],
            'test': pairs[n_train + n_val:]
        }
        
        logger.info(f"📊 Split sizes:")
        logger.info(f"   Train: {len(splits['train'])} ({len(splits['train'])/n_total:.1%})")
        logger.info(f"   Val:   {len(splits['val'])} ({len(splits['val'])/n_total:.1%})")
        logger.info(f"   Test:  {len(splits['test'])} ({len(splits['test'])/n_total:.1%})")
        
        return splits
    
    def copy_files(self, splits):
        """
        Copy files to appropriate train/val/test directories
        
        Args:
            splits: Dict with 'train', 'val', 'test' keys
        """
        logger.info("📦 Copying files to dataset structure...")
        
        for split_name, pairs in splits.items():
            logger.info(f"   Copying {len(pairs)} files to {split_name}...")
            
            for image_path, label_path in pairs:
                # Copy image
                dest_img = self.output_dir / 'images' / split_name / image_path.name
                shutil.copy2(image_path, dest_img)
                
                # Copy label
                dest_lbl = self.output_dir / 'labels' / split_name / label_path.name
                shutil.copy2(label_path, dest_lbl)
        
        logger.info("✅ All files copied")
    
    def clean_output_directory(self):
        """Remove existing output directory if it exists"""
        if self.output_dir.exists():
            logger.info(f"🗑️  Removing existing directory: {self.output_dir}")
            shutil.rmtree(self.output_dir)
    
    def prepare(self, clean=False):
        """
        Run the complete preparation process
        
        Args:
            clean: If True, remove existing output directory first
        """
        logger.info("=" * 60)
        logger.info("🚀 Starting Dataset Preparation")
        logger.info("=" * 60)
        
        # Clean if requested
        if clean:
            self.clean_output_directory()
        
        # Create directory structure
        self.create_directory_structure()
        
        # Find all image-label pairs
        pairs = self.find_image_label_pairs()
        
        if len(pairs) == 0:
            logger.error("❌ No image-label pairs found!")
            return False
        
        # Split dataset
        splits = self.split_dataset(pairs)
        
        # Copy files
        self.copy_files(splits)
        
        logger.info("=" * 60)
        logger.info("✅ Dataset preparation complete!")
        logger.info("=" * 60)
        logger.info(f"📁 Dataset ready at: {self.output_dir}")
        logger.info("")
        logger.info("🎯 Next steps:")
        logger.info("   1. Review dataset.yaml configuration")
        logger.info("   2. Train model: python backend/train_custom_model.py --dataset data/deer_dataset.yaml")
        
        return True

def main():
    parser = argparse.ArgumentParser(
        description='Prepare YOLO dataset from synthetic training images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default 70/20/10 split
  python backend/prepare_dataset.py \\
      --input data/synthetic_training \\
      --output data/training_data

  # Custom 80/15/5 split
  python backend/prepare_dataset.py \\
      --input data/synthetic_training \\
      --output data/training_data \\
      --split 80 15 5

  # Clean existing data first
  python backend/prepare_dataset.py \\
      --input data/synthetic_training \\
      --output data/training_data \\
      --clean
        """
    )
    
    parser.add_argument('--input', type=str, default='data/synthetic_training',
                       help='Input directory with synthetic images (default: data/synthetic_training)')
    parser.add_argument('--output', type=str, default='data/training_data',
                       help='Output directory for YOLO dataset (default: data/training_data)')
    parser.add_argument('--split', type=float, nargs=3, default=[70, 20, 10],
                       metavar=('TRAIN', 'VAL', 'TEST'),
                       help='Train/Val/Test split percentages (default: 70 20 10)')
    parser.add_argument('--clean', action='store_true',
                       help='Remove existing output directory first')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    
    args = parser.parse_args()
    
    # Set random seed for reproducibility
    random.seed(args.seed)
    
    # Create preparer
    preparer = DatasetPreparer(
        input_dir=args.input,
        output_dir=args.output,
        train_split=args.split[0],
        val_split=args.split[1],
        test_split=args.split[2]
    )
    
    # Run preparation
    success = preparer.prepare(clean=args.clean)
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main()
