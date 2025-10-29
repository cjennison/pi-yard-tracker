#!/usr/bin/env python3
"""
Dataset Cleanup Script

Removes all synthetic training data and prepared datasets to start fresh.

Usage:
    python backend/cleanup_dataset.py --all
    python backend/cleanup_dataset.py --synthetic-only
    python backend/cleanup_dataset.py --prepared-only
"""

import argparse
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatasetCleaner:
    """Cleans up training data directories"""
    
    def __init__(self):
        self.synthetic_dir = Path('data/synthetic_training')
        self.training_dir = Path('data/training_data')
        self.annotation_check_dir = Path('data/annotation_check')
        self.models_dir = Path('models/custom_model')
    
    def clean_synthetic_training(self):
        """Remove all synthetic training images and labels"""
        if self.synthetic_dir.exists():
            # Count files before deletion
            files = list(self.synthetic_dir.glob('*'))
            n_files = len(files)
            
            logger.info(f"🗑️  Removing {n_files} files from {self.synthetic_dir}")
            
            for file in files:
                file.unlink()
            
            logger.info(f"✅ Cleaned {self.synthetic_dir}")
        else:
            logger.info(f"ℹ️  {self.synthetic_dir} does not exist, skipping")
    
    def clean_prepared_dataset(self):
        """Remove prepared YOLO dataset structure"""
        if self.training_dir.exists():
            logger.info(f"🗑️  Removing {self.training_dir}")
            shutil.rmtree(self.training_dir)
            logger.info(f"✅ Cleaned {self.training_dir}")
        else:
            logger.info(f"ℹ️  {self.training_dir} does not exist, skipping")
    
    def clean_annotation_check(self):
        """Remove annotation visualization directory"""
        if self.annotation_check_dir.exists():
            logger.info(f"🗑️  Removing {self.annotation_check_dir}")
            shutil.rmtree(self.annotation_check_dir)
            logger.info(f"✅ Cleaned {self.annotation_check_dir}")
        else:
            logger.info(f"ℹ️  {self.annotation_check_dir} does not exist, skipping")
    
    def clean_trained_models(self):
        """Remove trained custom models"""
        if self.models_dir.exists():
            logger.info(f"🗑️  Removing {self.models_dir}")
            shutil.rmtree(self.models_dir)
            logger.info(f"✅ Cleaned {self.models_dir}")
        else:
            logger.info(f"ℹ️  {self.models_dir} does not exist, skipping")
    
    def clean_all(self):
        """Remove all generated data"""
        logger.info("=" * 60)
        logger.info("🧹 Cleaning ALL dataset files")
        logger.info("=" * 60)
        
        self.clean_synthetic_training()
        self.clean_prepared_dataset()
        self.clean_annotation_check()
        self.clean_trained_models()
        
        logger.info("=" * 60)
        logger.info("✅ Cleanup complete - ready for fresh start!")
        logger.info("=" * 60)

def main():
    parser = argparse.ArgumentParser(
        description='Clean up training datasets and models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Remove everything (synthetic data, prepared dataset, models)
  python backend/cleanup_dataset.py --all

  # Only remove synthetic training images
  python backend/cleanup_dataset.py --synthetic-only

  # Only remove prepared YOLO dataset
  python backend/cleanup_dataset.py --prepared-only

  # Remove models only
  python backend/cleanup_dataset.py --models-only
        """
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Remove all dataset files and models')
    parser.add_argument('--synthetic-only', action='store_true',
                       help='Only remove synthetic training images')
    parser.add_argument('--prepared-only', action='store_true',
                       help='Only remove prepared YOLO dataset')
    parser.add_argument('--models-only', action='store_true',
                       help='Only remove trained models')
    parser.add_argument('--annotation-check', action='store_true',
                       help='Also remove annotation check visualizations')
    
    args = parser.parse_args()
    
    # If no specific option, default to --all
    if not any([args.all, args.synthetic_only, args.prepared_only, args.models_only]):
        logger.warning("⚠️  No cleanup option specified, defaulting to --all")
        args.all = True
    
    cleaner = DatasetCleaner()
    
    if args.all:
        cleaner.clean_all()
    else:
        logger.info("=" * 60)
        logger.info("🧹 Starting selective cleanup")
        logger.info("=" * 60)
        
        if args.synthetic_only:
            cleaner.clean_synthetic_training()
        
        if args.prepared_only:
            cleaner.clean_prepared_dataset()
        
        if args.models_only:
            cleaner.clean_trained_models()
        
        if args.annotation_check:
            cleaner.clean_annotation_check()
        
        logger.info("=" * 60)
        logger.info("✅ Selective cleanup complete!")
        logger.info("=" * 60)

if __name__ == "__main__":
    main()
