"""
Training module for Pi Yard Tracker

Handles custom model training workflow including:
- Synthetic data generation
- Dataset preparation
- Model training
- Model testing and validation
- Annotation visualization
"""

from .generate_training_data import SyntheticDataGenerator
from .prepare_dataset import DatasetPreparer
from .cleanup_dataset import DatasetCleaner

__all__ = [
    'SyntheticDataGenerator',
    'DatasetPreparer', 
    'DatasetCleaner'
]
