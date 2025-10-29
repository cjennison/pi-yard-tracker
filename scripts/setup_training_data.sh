#!/bin/bash
# Prepare dataset structure for YOLO training
# This creates the proper folder structure needed for training

set -e

echo "🗂️  Creating YOLO dataset structure..."

# Base directory
BASE_DIR="data/training_data"

# Create directories
mkdir -p "$BASE_DIR/images/train"
mkdir -p "$BASE_DIR/images/val"
mkdir -p "$BASE_DIR/images/test"
mkdir -p "$BASE_DIR/labels/train"
mkdir -p "$BASE_DIR/labels/val"
mkdir -p "$BASE_DIR/labels/test"
mkdir -p "$BASE_DIR/raw_images"  # Put unannotated images here

echo "✅ Directory structure created:"
echo ""
echo "$BASE_DIR/"
echo "├── images/"
echo "│   ├── train/          # 70% of your annotated images"
echo "│   ├── val/            # 20% of your annotated images"
echo "│   └── test/           # 10% of your annotated images"
echo "├── labels/"
echo "│   ├── train/          # Matching .txt files for train images"
echo "│   ├── val/            # Matching .txt files for val images"
echo "│   └── test/           # Matching .txt files for test images"
echo "└── raw_images/         # Put your unannotated images here"
echo ""
echo "Next steps:"
echo "1. Copy your images to $BASE_DIR/raw_images/"
echo "2. Annotate them using Roboflow or LabelImg"
echo "3. Split into train/val/test (or let Roboflow do it)"
echo "4. Copy dataset.yaml.example to dataset.yaml and edit paths"
echo "5. Run: python backend/train_custom_model.py --dataset data/deer_dataset.yaml"
