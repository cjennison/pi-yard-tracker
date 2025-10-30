#!/bin/bash
# Setup script for Pi Yard Tracker

set -e  # Exit on error

echo "🐾 Pi Yard Tracker Setup"
echo "========================"
echo ""

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    PI_MODEL=$(cat /proc/device-tree/model)
    echo "📍 Detected: $PI_MODEL"
else
    echo "⚠️  Not running on Raspberry Pi - will use simulation mode"
fi

echo ""
echo "📦 Checking system dependencies..."
if ! dpkg -l | grep -q python3-picamera2; then
    echo "Installing picamera2..."
    sudo apt-get update -qq
    sudo apt-get install -y python3-picamera2 python3-libcamera
else
    echo "✅ picamera2 already installed"
fi

echo ""
echo "📦 Setting up Python virtual environment..."
python3 -m venv venv --system-site-packages
source venv/bin/activate

echo ""
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
if [ -s requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "ℹ️  No additional packages needed"
fi

echo ""
echo "📁 Creating data directories..."
mkdir -p data/photos
mkdir -p models

echo ""
echo "⚙️  Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file (edit if needed)"
else
    echo "ℹ️  .env already exists, skipping"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the camera capture system:"
echo "  source venv/bin/activate"
echo "  python backend/camera_capture.py"
echo ""
