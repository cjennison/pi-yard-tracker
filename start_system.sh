#!/bin/bash
# Pi Yard Tracker - Complete System Startup Script
#
# This script starts the complete system:
# 1. Camera capture (saves photos + detections to database)
# 2. Live streaming (WebSocket feed with detections)
# 3. FastAPI server (REST API + WebSocket endpoint)
# 4. Automatic cleanup service (deletes old photos)

echo "🐾 Starting Pi Yard Tracker System"
echo "===================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if already running
if pgrep -f "run_camera_system.py" > /dev/null; then
    echo "⚠️  System already running. Stop it first with: pkill -f run_camera_system.py"
    exit 1
fi

# Default configuration
PORT=${PORT:-8000}
MODEL=${MODEL:-models/custom_model/weights/best.pt}
CONFIDENCE=${CONFIDENCE:-0.25}
INTERVAL=${INTERVAL:-10.0}

echo ""
echo "Configuration:"
echo "  Port: $PORT"
echo "  Model: $MODEL"
echo "  Confidence: $CONFIDENCE"
echo "  Capture Interval: ${INTERVAL}s"
echo ""

# Start the complete system
echo "🚀 Starting camera system..."
python run_camera_system.py \
    --port $PORT \
    --model "$MODEL" \
    --confidence $CONFIDENCE \
    --interval $INTERVAL

# Note: This runs in foreground. Press Ctrl+C to stop.
