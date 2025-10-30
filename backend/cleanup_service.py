"""
Photo Cleanup Service

Automatically deletes old photo files from the filesystem while preserving
database records. This keeps the detection history intact while managing disk space.

The database will still contain all photo and detection records, but the actual
image files will be deleted after the retention period.

Usage:
    python backend/cleanup_service.py --retention-hours 24 --check-interval 300
"""

import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import argparse
import signal
import sys

try:
    from backend.database import get_db
except ImportError:
    # Try relative import if running as module
    try:
        from .database import get_db
    except ImportError:
        # If both fail, database stats won't be available
        get_db = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_PHOTO_DIR = Path("data/photos")
DEFAULT_RETENTION_HOURS = 1  # Keep photos for 1 hour
DEFAULT_CHECK_INTERVAL = 300  # Check every 5 minutes (300 seconds)


class PhotoCleanupService:
    """Service that periodically deletes old photo files"""
    
    def __init__(
        self,
        photo_dir: Path,
        retention_hours: int = DEFAULT_RETENTION_HOURS,
        check_interval: int = DEFAULT_CHECK_INTERVAL
    ):
        """
        Initialize cleanup service
        
        Args:
            photo_dir: Directory containing photos
            retention_hours: Hours to keep photo files (default: 24)
            check_interval: Seconds between cleanup checks (default: 300)
        """
        self.photo_dir = photo_dir
        self.retention_hours = retention_hours
        self.check_interval = check_interval
        self.running = False
        
        logger.info(f"📁 Photo directory: {self.photo_dir.absolute()}")
        logger.info(f"⏰ Retention period: {self.retention_hours} hours")
        logger.info(f"🔄 Check interval: {self.check_interval} seconds")
    
    def start(self):
        """Start the cleanup service"""
        self.running = True
        logger.info("🚀 Cleanup service started")
        
        # Note: Signal handlers can only be set in the main thread
        # When running as a daemon thread, the parent process handles signals
        
        try:
            while self.running:
                self._cleanup_old_photos()
                
                # Sleep in small intervals to allow for responsive shutdown
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
        
        except Exception as e:
            logger.error(f"❌ Cleanup service error: {e}")
            raise
        finally:
            logger.info("👋 Cleanup service stopped")
    
    def stop(self):
        """Stop the cleanup service"""
        logger.info("⏸️  Stopping cleanup service...")
        self.running = False
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📡 Received signal {signum}")
        self.stop()
    
    def _cleanup_old_photos(self):
        """Delete photo files older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        deleted_count = 0
        deleted_size = 0
        skipped_count = 0
        
        logger.debug(f"🔍 Checking for photos older than {cutoff_time.isoformat()}")
        
        # Find all .jpg files in photo directory (excluding subdirectories like detections/)
        for photo_path in self.photo_dir.glob("*.jpg"):
            try:
                # Get file modification time
                file_stat = photo_path.stat()
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                # Delete if older than cutoff
                if file_time < cutoff_time:
                    file_size = file_stat.st_size
                    photo_path.unlink()
                    deleted_count += 1
                    deleted_size += file_size
                    logger.debug(f"🗑️  Deleted: {photo_path.name} ({file_size / 1024:.1f} KB)")
                
            except FileNotFoundError:
                # File was already deleted (race condition)
                skipped_count += 1
                continue
            except Exception as e:
                logger.error(f"❌ Failed to delete {photo_path.name}: {e}")
                skipped_count += 1
        
        # Log summary if any files were deleted
        if deleted_count > 0:
            size_mb = deleted_size / (1024 * 1024)
            logger.info(f"🗑️  Deleted {deleted_count} old photo(s) ({size_mb:.2f} MB freed)")
            
            # Also delete corresponding detection visualization files
            self._cleanup_detection_visualizations(cutoff_time)
        
        if skipped_count > 0:
            logger.debug(f"⏭️  Skipped {skipped_count} file(s) (already deleted or error)")
    
    def _cleanup_detection_visualizations(self, cutoff_time: datetime):
        """Delete old detection visualization files"""
        detections_dir = self.photo_dir / "detections"
        
        if not detections_dir.exists():
            return
        
        deleted_count = 0
        
        for detection_path in detections_dir.glob("detected_*.jpg"):
            try:
                file_time = datetime.fromtimestamp(detection_path.stat().st_mtime)
                
                if file_time < cutoff_time:
                    detection_path.unlink()
                    deleted_count += 1
                    logger.debug(f"🗑️  Deleted detection: {detection_path.name}")
            
            except Exception as e:
                logger.debug(f"⚠️  Failed to delete {detection_path.name}: {e}")
        
        if deleted_count > 0:
            logger.info(f"🗑️  Deleted {deleted_count} old detection visualization(s)")
    
    def get_stats(self) -> dict:
        """Get current storage statistics"""
        total_photos = 0
        total_size = 0
        
        for photo_path in self.photo_dir.glob("*.jpg"):
            try:
                total_photos += 1
                total_size += photo_path.stat().st_size
            except:
                continue
        
        # Get database stats
        db_stats = None
        if get_db is not None:
            try:
                db = get_db()
                db_stats = db.get_stats()
            except Exception as e:
                logger.debug(f"⚠️  Could not get database stats: {e}")
        
        return {
            "filesystem": {
                "photo_files": total_photos,
                "total_size_mb": total_size / (1024 * 1024)
            },
            "database": db_stats
        }


def main():
    """Run the cleanup service"""
    parser = argparse.ArgumentParser(
        description='Photo Cleanup Service - Automatically delete old photo files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: delete files older than 24 hours, check every 5 minutes
  python backend/cleanup_service.py
  
  # Custom retention: 48 hours
  python backend/cleanup_service.py --retention-hours 48
  
  # Check more frequently: every 1 minute
  python backend/cleanup_service.py --check-interval 60
  
  # Both custom
  python backend/cleanup_service.py --retention-hours 12 --check-interval 300

Note: Database records are preserved. Only image files are deleted.
        """
    )
    
    parser.add_argument(
        '--photo-dir',
        type=str,
        default=str(DEFAULT_PHOTO_DIR),
        help=f'Photo directory path (default: {DEFAULT_PHOTO_DIR})'
    )
    
    parser.add_argument(
        '--retention-hours',
        type=int,
        default=DEFAULT_RETENTION_HOURS,
        help=f'Hours to keep photo files (default: {DEFAULT_RETENTION_HOURS})'
    )
    
    parser.add_argument(
        '--check-interval',
        type=int,
        default=DEFAULT_CHECK_INTERVAL,
        help=f'Seconds between cleanup checks (default: {DEFAULT_CHECK_INTERVAL})'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show current storage statistics and exit'
    )
    
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run cleanup once and exit (useful for cron jobs)'
    )
    
    args = parser.parse_args()
    
    # Create service
    photo_dir = Path(args.photo_dir)
    service = PhotoCleanupService(
        photo_dir=photo_dir,
        retention_hours=args.retention_hours,
        check_interval=args.check_interval
    )
    
    # Handle different run modes
    if args.stats:
        # Show stats and exit
        logger.info("📊 Current Storage Statistics:")
        stats = service.get_stats()
        
        fs = stats['filesystem']
        logger.info(f"   📁 Filesystem: {fs['photo_files']} files ({fs['total_size_mb']:.2f} MB)")
        
        if stats['database']:
            db = stats['database']
            logger.info(f"   💾 Database: {db['total_photos']} photos, {db['total_detections']} detections")
        
        sys.exit(0)
    
    elif args.run_once:
        # Run cleanup once and exit
        logger.info("🔄 Running cleanup (single pass)...")
        service._cleanup_old_photos()
        logger.info("✅ Cleanup complete")
        sys.exit(0)
    
    else:
        # Run as continuous service
        logger.info("=" * 60)
        logger.info("🧹 Pi Yard Tracker - Photo Cleanup Service")
        logger.info("=" * 60)
        service.start()


if __name__ == "__main__":
    main()
