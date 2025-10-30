#!/usr/bin/env python3
"""
Fetch Retraining Photos from Azure Blob Storage

This script downloads all photos marked for retraining from Azure Blob Storage
and optionally deletes them from the cloud after successful download.

Usage:
    python backend/training/fetch_retraining_photos.py --output data/to_annotate
    python backend/training/fetch_retraining_photos.py --output data/to_annotate --delete
"""

import os
import argparse
import logging
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_blob_service_client() -> BlobServiceClient:
    """Get Azure Blob Storage client"""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    
    if not connection_string:
        raise ValueError(
            "❌ AZURE_STORAGE_CONNECTION_STRING not set in .env file\n"
            "   Get your connection string from: Azure Portal > Storage Account > Access Keys"
        )
    
    return BlobServiceClient.from_connection_string(connection_string)


def list_blobs(blob_service_client: BlobServiceClient, container_name: str) -> List[str]:
    """
    List all blobs in the container
    
    Args:
        blob_service_client: Azure Blob Storage client
        container_name: Name of the container
    
    Returns:
        List of blob names
    """
    try:
        container_client = blob_service_client.get_container_client(container_name)
        blob_list = container_client.list_blobs()
        return [blob.name for blob in blob_list]
    except Exception as e:
        logger.error(f"❌ Failed to list blobs: {e}")
        return []


def download_blob(
    blob_service_client: BlobServiceClient,
    container_name: str,
    blob_name: str,
    output_path: Path
) -> bool:
    """
    Download a single blob
    
    Args:
        blob_service_client: Azure Blob Storage client
        container_name: Name of the container
        blob_name: Name of the blob to download
        output_path: Local path to save the file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        # Download blob data
        with open(output_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        
        logger.info(f"⬇️  Downloaded: {blob_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download {blob_name}: {e}")
        return False


def delete_blob(
    blob_service_client: BlobServiceClient,
    container_name: str,
    blob_name: str
) -> bool:
    """
    Delete a single blob
    
    Args:
        blob_service_client: Azure Blob Storage client
        container_name: Name of the container
        blob_name: Name of the blob to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        blob_client.delete_blob()
        logger.info(f"🗑️  Deleted from cloud: {blob_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to delete {blob_name}: {e}")
        return False


def fetch_retraining_photos(
    output_dir: Path,
    delete_after_download: bool = False
) -> Tuple[int, int]:
    """
    Fetch all retraining photos from Azure Blob Storage
    
    Args:
        output_dir: Directory to save downloaded photos
        delete_after_download: If True, delete blobs after successful download
    
    Returns:
        Tuple of (downloaded_count, deleted_count)
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get Azure configuration
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "retraining-photos")
    
    try:
        # Get blob service client
        blob_service_client = get_blob_service_client()
        
        # List all blobs
        blob_names = list_blobs(blob_service_client, container_name)
        
        if not blob_names:
            logger.info("ℹ️  No photos found in cloud storage")
            return 0, 0
        
        logger.info(f"📦 Found {len(blob_names)} photo(s) in cloud storage")
        logger.info(f"📁 Downloading to: {output_dir.absolute()}")
        
        downloaded_count = 0
        deleted_count = 0
        
        # Download each blob
        for blob_name in blob_names:
            output_path = output_dir / blob_name
            
            # Skip if file already exists locally
            if output_path.exists():
                logger.info(f"⏭️  Skipping {blob_name} (already exists locally)")
                
                # Still delete from cloud if requested
                if delete_after_download:
                    if delete_blob(blob_service_client, container_name, blob_name):
                        deleted_count += 1
                
                continue
            
            # Download blob
            if download_blob(blob_service_client, container_name, blob_name, output_path):
                downloaded_count += 1
                
                # Delete from cloud if requested
                if delete_after_download:
                    if delete_blob(blob_service_client, container_name, blob_name):
                        deleted_count += 1
        
        return downloaded_count, deleted_count
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch retraining photos: {e}")
        return 0, 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Fetch retraining photos from Azure Blob Storage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download to default directory
  python backend/training/fetch_retraining_photos.py
  
  # Download to custom directory
  python backend/training/fetch_retraining_photos.py --output custom/path
  
  # Download and delete from cloud
  python backend/training/fetch_retraining_photos.py --delete
  
  # Download, delete, and create empty annotation files (hard negatives)
  python backend/training/fetch_retraining_photos.py --delete --create-empty-annotations

Environment Variables Required:
  AZURE_STORAGE_CONNECTION_STRING - Azure Storage connection string
  AZURE_STORAGE_CONTAINER_NAME - Container name (default: retraining-photos)
        """
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='data/to_annotate',
        help='Output directory for downloaded photos (default: data/to_annotate)'
    )
    
    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete photos from cloud storage after successful download'
    )
    
    parser.add_argument(
        '--create-empty-annotations',
        action='store_true',
        help='Create empty .txt annotation files (for hard negative training)'
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    
    logger.info("☁️  Fetching retraining photos from Azure Blob Storage")
    logger.info("=" * 60)
    
    # Fetch photos
    downloaded, deleted = fetch_retraining_photos(
        output_dir=output_dir,
        delete_after_download=args.delete
    )
    
    logger.info("")
    logger.info("📊 Summary:")
    logger.info(f"   Downloaded: {downloaded} photo(s)")
    if args.delete:
        logger.info(f"   Deleted from cloud: {deleted} photo(s)")
    logger.info(f"   Location: {output_dir.absolute()}")
    
    # Create empty annotation files if requested
    if args.create_empty_annotations and downloaded > 0:
        logger.info("")
        logger.info("📝 Creating empty annotation files (hard negatives)...")
        
        created = 0
        for img_file in output_dir.glob("*.jpg"):
            txt_file = img_file.with_suffix('.txt')
            if not txt_file.exists():
                txt_file.touch()
                created += 1
        
        for img_file in output_dir.glob("*.jpeg"):
            txt_file = img_file.with_suffix('.txt')
            if not txt_file.exists():
                txt_file.touch()
                created += 1
        
        logger.info(f"   Created {created} empty annotation file(s)")
    
    logger.info("")
    logger.info("ℹ️  Next steps:")
    logger.info("   1. Review photos and annotations in the output directory")
    logger.info("   2. Add/edit annotations as needed (YOLO format)")
    logger.info("   3. Run: python backend/training/prepare_dataset.py")
    logger.info("   4. Run: python backend/training/train_custom_model.py")


if __name__ == "__main__":
    main()
