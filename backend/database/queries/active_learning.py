"""
Active learning query functions

Handles marking photos for retraining and managing the annotation workflow.
"""

import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..db import get_db

logger = logging.getLogger(__name__)


def mark_photo_for_retraining(photo_id: int, to_annotate_dir: Path = Path("data/to_annotate")) -> bool:
    """
    Mark a photo for retraining and copy it to annotation directory
    
    Args:
        photo_id: ID of the photo to mark
        to_annotate_dir: Directory to copy photo to for annotation
    
    Returns:
        True if successful, False otherwise
    """
    db = get_db()
    
    try:
        # Get photo details
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, filepath, filename, marked_for_retraining FROM photos WHERE id = ?",
                (photo_id,)
            )
            photo = cursor.fetchone()
            
            if not photo:
                logger.warning(f"⚠️  Photo {photo_id} not found")
                return False
            
            # Check if already marked
            if photo['marked_for_retraining']:
                logger.info(f"ℹ️  Photo {photo_id} already marked for retraining")
                return True
            
            # Create to_annotate directory if it doesn't exist
            to_annotate_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy photo to annotation directory
            source_path = Path(photo['filepath'])
            if not source_path.exists():
                logger.error(f"❌ Photo file not found: {source_path}")
                return False
            
            dest_path = to_annotate_dir / photo['filename']
            shutil.copy2(source_path, dest_path)
            logger.info(f"📋 Copied {photo['filename']} to {to_annotate_dir}")
            
            # Update database
            cursor.execute(
                """
                UPDATE photos 
                SET marked_for_retraining = 1, marked_at = ? 
                WHERE id = ?
                """,
                (datetime.now().isoformat(), photo_id)
            )
            conn.commit()
            
            logger.info(f"✅ Marked photo {photo_id} for retraining")
            return True
        
    except Exception as e:
        logger.error(f"❌ Failed to mark photo for retraining: {e}")
        return False


def unmark_photo_for_retraining(photo_id: int) -> bool:
    """
    Unmark a photo for retraining (does not delete from to_annotate folder)
    
    Args:
        photo_id: ID of the photo to unmark
    
    Returns:
        True if successful, False otherwise
    """
    db = get_db()
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE photos 
                SET marked_for_retraining = 0, marked_at = NULL 
                WHERE id = ?
                """,
                (photo_id,)
            )
            conn.commit()
            
            logger.info(f"✅ Unmarked photo {photo_id} for retraining")
            return True
        
    except Exception as e:
        logger.error(f"❌ Failed to unmark photo for retraining: {e}")
        return False


def get_marked_photos(limit: Optional[int] = None, offset: int = 0):
    """
    Get all photos marked for retraining
    
    Args:
        limit: Maximum number of photos to return
        offset: Number of photos to skip
    
    Returns:
        List of photo dictionaries
    """
    db = get_db()
    
    query = """
        SELECT * FROM photos 
        WHERE marked_for_retraining = 1 
        ORDER BY marked_at DESC
    """
    
    if limit:
        query += f" LIMIT {limit} OFFSET {offset}"
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
    
    from ..models import Photo
    return [Photo.from_row(row).to_dict() for row in rows]


def get_marked_photos_count() -> int:
    """
    Get count of photos marked for retraining
    
    Returns:
        Number of marked photos
    """
    db = get_db()
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM photos WHERE marked_for_retraining = 1")
        result = cursor.fetchone()
    
    return result['count'] if result else 0
