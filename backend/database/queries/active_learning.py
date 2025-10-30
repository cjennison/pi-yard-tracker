"""
Active learning query functions

Handles marking photos for retraining and uploading to Azure Blob Storage.
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, ContentSettings

from ..db import get_db

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def _get_blob_service_client() -> Optional[BlobServiceClient]:
    """Get Azure Blob Storage client"""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    
    if not connection_string:
        logger.warning("⚠️  AZURE_STORAGE_CONNECTION_STRING not set in .env")
        return None
    
    try:
        return BlobServiceClient.from_connection_string(connection_string)
    except Exception as e:
        logger.error(f"❌ Failed to create Azure Blob client: {e}")
        return None


def _upload_to_blob_storage(photo_path: Path, photo_filename: str) -> bool:
    """
    Upload photo to Azure Blob Storage
    
    Args:
        photo_path: Local path to photo file
        photo_filename: Name of the file
    
    Returns:
        True if successful, False otherwise
    """
    blob_client_service = _get_blob_service_client()
    if not blob_client_service:
        return False
    
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "retraining-photos")
    
    try:
        # Get container client (create container if it doesn't exist)
        container_client = blob_client_service.get_container_client(container_name)
        try:
            container_client.create_container()
            logger.info(f"📦 Created container: {container_name}")
        except Exception:
            # Container already exists, that's fine
            pass
        
        # Upload file
        blob_client = container_client.get_blob_client(photo_filename)
        
        with open(photo_path, "rb") as data:
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type="image/jpeg")
            )
        
        logger.info(f"☁️  Uploaded {photo_filename} to Azure Blob Storage")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to upload to blob storage: {e}")
        return False


def mark_photo_for_retraining(photo_id: int) -> bool:
    """
    Mark a photo for retraining and upload to Azure Blob Storage
    
    Args:
        photo_id: ID of the photo to mark
    
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
            
            # Check if photo file exists
            source_path = Path(photo['filepath'])
            if not source_path.exists():
                logger.error(f"❌ Photo file not found: {source_path}")
                return False
            
            # Upload to Azure Blob Storage
            if not _upload_to_blob_storage(source_path, photo['filename']):
                logger.error(f"❌ Failed to upload {photo['filename']} to cloud storage")
                return False
            
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
            
            logger.info(f"✅ Marked photo {photo_id} for retraining and uploaded to cloud")
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
