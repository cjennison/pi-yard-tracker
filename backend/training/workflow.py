#!/usr/bin/env python3
"""
Complete Training Workflow Script

Orchestrates the entire custom model training pipeline:
1. Generate synthetic training data
2. Prepare dataset (train/val/test split)
3. Visualize annotations
4. Train custom model
5. Test custom model

Usage:
    # Full workflow with outdoor base image
    python backend/workflow.py --base-image photos/backyard.jpg --count 100
    
    # Full workflow generating from scratch
    python backend/workflow.py --background "outdoor meadow with grass" --count 50
    
    # Just generate and prepare (skip training)
    python backend/workflow.py --count 50 --skip-training
    
    # Resume training with existing data
    python backend/workflow.py --skip-generation --epochs 100
"""

import argparse
import subprocess
import sys
from pathlib import Path
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrainingWorkflow:
    """Orchestrates the complete training pipeline"""
    
    def __init__(self, args):
        self.args = args
        self.base_dir = Path('.')
        self.synthetic_dir = Path('data/synthetic_training')
        self.training_dir = Path('data/training_data')
        
    def run_step(self, step_name, command, check=True):
        """Run a pipeline step with logging"""
        logger.info("=" * 80)
        logger.info(f"🚀 STEP: {step_name}")
        logger.info("=" * 80)
        logger.info(f"Command: {' '.join(command)}")
        logger.info("")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                check=check,
                capture_output=False,
                text=True
            )
            
            elapsed = time.time() - start_time
            logger.info("")
            logger.info(f"✅ {step_name} completed in {elapsed:.1f}s")
            logger.info("")
            
            return result.returncode == 0
            
        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start_time
            logger.error("")
            logger.error(f"❌ {step_name} failed after {elapsed:.1f}s")
            logger.error(f"Error: {e}")
            logger.error("")
            
            if check:
                sys.exit(1)
            return False
    
    def step_generate_data(self):
        """Step 1: Generate synthetic training data"""
        if self.args.skip_generation:
            logger.info("⏭️  Skipping data generation (--skip-generation)")
            return True
        
        cmd = [
            'python', 'backend/generate_training_data.py',
            '--object', self.args.object,
            '--count', str(self.args.count)
        ]
        
        if self.args.base_image:
            cmd.extend(['--base-image', self.args.base_image])
        elif self.args.background:
            cmd.extend(['--background', self.args.background])
        
        return self.run_step("Generate Synthetic Data", cmd)
    
    def step_prepare_dataset(self):
        """Step 2: Prepare dataset into train/val/test split"""
        if self.args.skip_preparation:
            logger.info("⏭️  Skipping dataset preparation (--skip-preparation)")
            return True
        
        cmd = [
            'python', 'backend/prepare_dataset.py',
            '--input', str(self.synthetic_dir),
            '--output', str(self.training_dir),
            '--split', str(self.args.train), str(self.args.val), str(self.args.test),
            '--seed', str(self.args.seed)
        ]
        
        if self.args.clean:
            cmd.append('--clean')
        
        return self.run_step("Prepare Dataset", cmd)
    
    def step_visualize_annotations(self):
        """Step 3: Visualize annotations for verification"""
        if self.args.skip_visualization:
            logger.info("⏭️  Skipping annotation visualization (--skip-visualization)")
            return True
        
        # Visualize a sample from the training set
        sample_dir = self.training_dir / 'images' / 'train'
        if not sample_dir.exists():
            logger.warning(f"⚠️  Training directory doesn't exist: {sample_dir}")
            return True
        
        cmd = [
            'python', 'backend/visualize_annotations.py',
            '--input', str(self.training_dir / 'images' / 'train'),
            '--output', 'data/annotation_check'
        ]
        
        return self.run_step("Visualize Annotations", cmd)
    
    def step_train_model(self):
        """Step 4: Train custom model"""
        if self.args.skip_training:
            logger.info("⏭️  Skipping model training (--skip-training)")
            return True
        
        cmd = [
            'python', 'backend/train_custom_model.py',
            '--dataset', self.args.dataset,
            '--epochs', str(self.args.epochs),
            '--batch', str(self.args.batch),
            '--img-size', str(self.args.imgsz),
            '--model', self.args.model
        ]
        
        return self.run_step("Train Custom Model", cmd)
    
    def step_test_model(self):
        """Step 5: Test trained model"""
        if self.args.skip_testing:
            logger.info("⏭️  Skipping model testing (--skip-testing)")
            return True
        
        model_path = Path('models/custom_model/weights/best.pt')
        if not model_path.exists():
            logger.warning(f"⚠️  Trained model not found: {model_path}")
            logger.warning("⚠️  Skipping testing")
            return True
        
        # Test on validation set
        test_dir = self.training_dir / 'images' / 'val'
        if not test_dir.exists():
            logger.warning(f"⚠️  Validation directory doesn't exist: {test_dir}")
            return True
        
        cmd = [
            'python', 'backend/test_custom_model.py',
            '--model', str(model_path),
            '--images-dir', str(test_dir),
            '--conf', str(self.args.conf),
            '--save-results'
        ]
        
        return self.run_step("Test Custom Model", cmd)
    
    def run(self):
        """Execute the complete workflow"""
        logger.info("")
        logger.info("🎯" * 40)
        logger.info("CUSTOM MODEL TRAINING WORKFLOW")
        logger.info("🎯" * 40)
        logger.info("")
        logger.info(f"Configuration:")
        logger.info(f"  Object: {self.args.object}")
        logger.info(f"  Count: {self.args.count}")
        logger.info(f"  Base Image: {self.args.base_image or 'None (generate from scratch)'}")
        logger.info(f"  Background: {self.args.background or 'N/A'}")
        logger.info(f"  Train/Val/Test Split: {self.args.train}/{self.args.val}/{self.args.test}")
        logger.info(f"  Epochs: {self.args.epochs}")
        logger.info(f"  Batch Size: {self.args.batch}")
        logger.info("")
        
        steps = [
            ("Generate Data", self.step_generate_data),
            ("Prepare Dataset", self.step_prepare_dataset),
            ("Visualize Annotations", self.step_visualize_annotations),
            ("Train Model", self.step_train_model),
            ("Test Model", self.step_test_model)
        ]
        
        start_time = time.time()
        
        for step_name, step_func in steps:
            success = step_func()
            if not success and not self.args.continue_on_error:
                logger.error(f"❌ Workflow failed at step: {step_name}")
                sys.exit(1)
        
        total_time = time.time() - start_time
        
        logger.info("")
        logger.info("🎉" * 40)
        logger.info(f"WORKFLOW COMPLETE in {total_time/60:.1f} minutes!")
        logger.info("🎉" * 40)
        logger.info("")
        logger.info("📊 Results:")
        logger.info(f"  Synthetic data: {self.synthetic_dir}")
        logger.info(f"  Prepared dataset: {self.training_dir}")
        logger.info(f"  Trained model: models/custom_model/weights/best.pt")
        logger.info(f"  Annotation checks: data/annotation_check")
        logger.info("")

def main():
    parser = argparse.ArgumentParser(
        description='Complete training workflow for custom YOLO model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full workflow with outdoor base image (RECOMMENDED)
  python backend/workflow.py --base-image photos/backyard.jpg --count 100 --epochs 100

  # Full workflow generating from scratch
  python backend/workflow.py --background "outdoor meadow with grass" --count 50

  # Just generate and prepare (skip training)
  python backend/workflow.py --count 50 --skip-training

  # Resume training with existing data
  python backend/workflow.py --skip-generation --skip-preparation --epochs 100
        """
    )
    
    # Generation options
    gen_group = parser.add_argument_group('Data Generation')
    gen_group.add_argument('--object', type=str, default='white-tailed deer',
                          help='Object to detect (default: white-tailed deer)')
    gen_group.add_argument('--count', type=int, default=50,
                          help='Number of images to generate (default: 50)')
    gen_group.add_argument('--base-image', type=str,
                          help='Base image for scene-matching generation')
    gen_group.add_argument('--background', type=str,
                          help='Background description for from-scratch generation')
    
    # Dataset preparation options
    prep_group = parser.add_argument_group('Dataset Preparation')
    prep_group.add_argument('--train', type=int, default=70,
                           help='Training set percentage (default: 70)')
    prep_group.add_argument('--val', type=int, default=20,
                           help='Validation set percentage (default: 20)')
    prep_group.add_argument('--test', type=int, default=10,
                           help='Test set percentage (default: 10)')
    prep_group.add_argument('--seed', type=int, default=42,
                           help='Random seed for reproducible splits (default: 42)')
    prep_group.add_argument('--clean', action='store_true',
                           help='Clean existing prepared dataset before preparing')
    
    # Training options
    train_group = parser.add_argument_group('Model Training')
    train_group.add_argument('--dataset', type=str, default='data/deer_dataset.yaml',
                            help='Dataset YAML config (default: data/deer_dataset.yaml)')
    train_group.add_argument('--epochs', type=int, default=50,
                            help='Number of training epochs (default: 50)')
    train_group.add_argument('--batch', type=int, default=16,
                            help='Batch size (default: 16)')
    train_group.add_argument('--imgsz', type=int, default=640,
                            help='Image size (default: 640)')
    train_group.add_argument('--model', type=str, default='n',
                            help='Model size: n, s, m, l, x (default: n)')
    
    # Testing options
    test_group = parser.add_argument_group('Model Testing')
    test_group.add_argument('--conf', type=float, default=0.25,
                           help='Confidence threshold for testing (default: 0.25)')
    
    # Workflow control
    control_group = parser.add_argument_group('Workflow Control')
    control_group.add_argument('--skip-generation', action='store_true',
                              help='Skip data generation step')
    control_group.add_argument('--skip-preparation', action='store_true',
                              help='Skip dataset preparation step')
    control_group.add_argument('--skip-visualization', action='store_true',
                              help='Skip annotation visualization step')
    control_group.add_argument('--skip-training', action='store_true',
                              help='Skip model training step')
    control_group.add_argument('--skip-testing', action='store_true',
                              help='Skip model testing step')
    control_group.add_argument('--continue-on-error', action='store_true',
                              help='Continue workflow even if a step fails')
    
    args = parser.parse_args()
    
    # Validation
    if not args.base_image and not args.background and not args.skip_generation:
        parser.error("Must specify either --base-image or --background (unless --skip-generation)")
    
    if args.train + args.val + args.test != 100:
        parser.error(f"Train/val/test split must sum to 100, got {args.train + args.val + args.test}")
    
    workflow = TrainingWorkflow(args)
    workflow.run()

if __name__ == "__main__":
    main()
