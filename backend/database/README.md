# Database Module

SQLite database interface for storing photos and detection results.

## Structure

- `schema.sql` - Database schema definition (tables, indexes)
- `db.py` - Database connection manager and low-level operations
- `models.py` - Python dataclasses representing database records
- `queries.py` - High-level CRUD operations for photos, detections, and sessions

## Database Schema

### Photos Table

Stores metadata for captured photos:

- `id` - Primary key
- `filename` - Photo filename
- `filepath` - Full path to photo file
- `width`, `height` - Image dimensions
- `captured_at` - When photo was taken
- `has_detections` - Boolean flag
- `detection_count` - Number of detections found

### Detections Table

Stores individual object detections:

- `id` - Primary key
- `photo_id` - Foreign key to photos
- `class_name` - Detected object class (e.g., "coffee_mug", "deer")
- `confidence` - Detection confidence (0.0-1.0)
- `bbox_x`, `bbox_y`, `bbox_width`, `bbox_height` - Normalized bounding box (0-1)
- `model_name` - Which YOLO model was used

### Detection Sessions Table

Tracks camera capture sessions:

- `id` - Primary key
- `started_at`, `ended_at` - Session timespan
- `model_name` - Model used in session
- `confidence_threshold` - Confidence setting
- `photo_count`, `detection_count` - Session statistics

## Usage

### Basic Operations

```python
from backend.database import (
    create_photo,
    create_detection,
    get_photos,
    get_detections,
    get_detection_stats
)

# Create photo record
photo_id = create_photo(
    filename="yard_001.jpg",
    filepath="/data/photos/yard_001.jpg",
    width=1920,
    height=1080
)

# Create detection record
detection_id = create_detection(
    photo_id=photo_id,
    class_name="coffee_mug",
    confidence=0.85,
    bbox_x=0.5,      # Center x (normalized)
    bbox_y=0.5,      # Center y (normalized)
    bbox_width=0.3,  # Width (normalized)
    bbox_height=0.4, # Height (normalized)
    model_name="custom_model/weights/best.pt"
)

# Update photo with detection count
from backend.database import update_photo_detections
update_photo_detections(photo_id, detection_count=1)

# Query photos with detections
photos = get_photos(has_detections=True, limit=50)

# Query detections by class
coffee_detections = get_detections(class_name="coffee_mug", min_confidence=0.5)

# Get statistics
stats = get_detection_stats()
print(f"Total photos: {stats['total_photos']}")
print(f"Total detections: {stats['total_detections']}")
```

### Session Tracking

```python
from backend.database import create_session, end_session

# Start session
session_id = create_session(
    model_name="custom_model/weights/best.pt",
    confidence_threshold=0.25
)

# ... capture photos and detect objects ...

# End session
end_session(session_id, photo_count=100, detection_count=35)
```

### Advanced Queries

```python
from datetime import datetime, timedelta
from backend.database import get_photos, get_detections

# Photos from last 24 hours
yesterday = datetime.now() - timedelta(days=1)
recent_photos = get_photos(start_date=yesterday)

# High-confidence detections
high_conf = get_detections(min_confidence=0.8)

# Pagination
page_1 = get_photos(limit=20, offset=0)
page_2 = get_photos(limit=20, offset=20)
```

## Database Location

Default: `data/detections.db`

Can be customized via environment variable or constructor:

```python
from backend.database import Database
from pathlib import Path

db = Database(db_path=Path("custom/path/detections.db"))
```
