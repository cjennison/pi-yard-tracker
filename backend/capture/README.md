# Camera Capture Module

Handles image capture from Raspberry Pi camera module (picamera2).

## Scripts

### `camera_capture.py`
Continuous image capture at configurable intervals.

**Usage:**
```bash
python backend/capture/camera_capture.py --interval 1.0 --output data/photos
```

**Features:**
- 1 FPS capture rate (configurable)
- Auto-cleanup of images older than 24 hours
- Timestamp-based filenames
- Logging with emoji indicators

**Dependencies:**
- picamera2 (system-wide installation required)
- pillow

**Note:** Must run on Raspberry Pi with camera module connected.
