-- Pi Yard Tracker Database Schema
-- SQLite database for storing photos and detection results

-- Photos table: stores metadata for captured photos
CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    filepath TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    has_detections BOOLEAN NOT NULL DEFAULT 0,
    detection_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Detections table: stores individual object detections
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    photo_id INTEGER NOT NULL,
    class_name TEXT NOT NULL,
    confidence REAL NOT NULL,
    bbox_x REAL NOT NULL,      -- Bounding box center x (normalized 0-1)
    bbox_y REAL NOT NULL,      -- Bounding box center y (normalized 0-1)
    bbox_width REAL NOT NULL,  -- Bounding box width (normalized 0-1)
    bbox_height REAL NOT NULL, -- Bounding box height (normalized 0-1)
    model_name TEXT,           -- Which model was used
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (photo_id) REFERENCES photos (id) ON DELETE CASCADE
);

-- Detection sessions: track when the camera was running
CREATE TABLE IF NOT EXISTS detection_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    model_name TEXT,
    confidence_threshold REAL,
    photo_count INTEGER DEFAULT 0,
    detection_count INTEGER DEFAULT 0
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_photos_captured_at ON photos(captured_at);
CREATE INDEX IF NOT EXISTS idx_photos_has_detections ON photos(has_detections);
CREATE INDEX IF NOT EXISTS idx_detections_photo_id ON detections(photo_id);
CREATE INDEX IF NOT EXISTS idx_detections_class_name ON detections(class_name);
CREATE INDEX IF NOT EXISTS idx_detections_created_at ON detections(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON detection_sessions(started_at);
