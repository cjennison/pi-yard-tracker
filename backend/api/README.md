# API Module

FastAPI REST API for querying photos and detections.

## Structure

- `main.py` - FastAPI application setup and configuration
- `schemas.py` - Pydantic models for request/response validation
- `routes/` - API endpoint handlers
  - `photos.py` - Photo endpoints
  - `detections.py` - Detection endpoints
  - `stats.py` - Statistics and session endpoints

## Running the API

### Development Mode (with auto-reload)

```bash
cd /home/cjennison/src/pi-yard-tracker
source venv/bin/activate
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode

```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health & Info

- `GET /` - API information
- `GET /health` - Health check with database status

### Photos

- `GET /photos/` - List photos with filtering
  - Query params: `limit`, `offset`, `has_detections`, `start_date`, `end_date`
- `GET /photos/{id}` - Get specific photo with detections
- `GET /photos/{id}/detections` - Get detections for specific photo

### Detections

- `GET /detections/` - List detections with filtering
  - Query params: `limit`, `offset`, `class_name`, `min_confidence`, `start_date`, `end_date`
- `GET /detections/classes` - Get all detected classes with counts

### Statistics

- `GET /stats` - Overall detection statistics
- `GET /sessions` - Recent detection sessions

## Interactive Documentation

Once the API is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Example API Calls

### Get Recent Photos

```bash
curl http://localhost:8000/photos/?limit=10
```

### Get Photos with Detections

```bash
curl http://localhost:8000/photos/?has_detections=true&limit=20
```

### Get Coffee Mug Detections

```bash
curl http://localhost:8000/detections/?class_name=coffee_mug&min_confidence=0.5
```

### Get Statistics

```bash
curl http://localhost:8000/stats
```

### Get Detection Classes

```bash
curl http://localhost:8000/detections/classes
```

## Response Examples

### Photo Response

```json
{
  "id": 42,
  "filename": "yard_20251029_100000.jpg",
  "filepath": "/data/photos/yard_20251029_100000.jpg",
  "width": 1920,
  "height": 1080,
  "captured_at": "2025-10-29T10:00:00",
  "has_detections": true,
  "detection_count": 2,
  "created_at": "2025-10-29T10:00:00"
}
```

### Detection Response

```json
{
  "id": 1,
  "photo_id": 42,
  "class_name": "coffee_mug",
  "confidence": 0.85,
  "bbox": {
    "x": 0.5,
    "y": 0.5,
    "width": 0.3,
    "height": 0.4
  },
  "model_name": "custom_model/weights/best.pt",
  "created_at": "2025-10-29T10:00:00"
}
```

### Stats Response

```json
{
  "total_photos": 150,
  "photos_with_detections": 45,
  "total_detections": 67,
  "detection_classes": [
    { "class": "coffee_mug", "count": 35 },
    { "class": "person", "count": 20 },
    { "class": "cat", "count": 12 }
  ]
}
```

## Pagination

All list endpoints support pagination:

```bash
# First page (20 items)
curl http://localhost:8000/photos/?limit=20&offset=0

# Second page (20 items)
curl http://localhost:8000/photos/?limit=20&offset=20

# Third page (20 items)
curl http://localhost:8000/photos/?limit=20&offset=40
```

## Filtering by Date

Use ISO 8601 datetime format:

```bash
# Photos from today
curl http://localhost:8000/photos/?start_date=2025-10-29T00:00:00

# Detections from specific time range
curl "http://localhost:8000/detections/?start_date=2025-10-29T10:00:00&end_date=2025-10-29T12:00:00"
```

## CORS Configuration

Currently allows all origins for development. For production, update `backend/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
```
