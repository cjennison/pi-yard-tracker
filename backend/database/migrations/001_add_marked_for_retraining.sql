-- Migration: Add marked_for_retraining column to photos table
-- This enables the Active Learning workflow where users can mark photos
-- that had detection misses for later annotation and retraining

-- Add column to photos table
ALTER TABLE photos ADD COLUMN marked_for_retraining BOOLEAN NOT NULL DEFAULT 0;

-- Add index for filtering marked photos
CREATE INDEX IF NOT EXISTS idx_photos_marked_for_retraining ON photos(marked_for_retraining);

-- Add column to track when photo was marked
ALTER TABLE photos ADD COLUMN marked_at TIMESTAMP;
