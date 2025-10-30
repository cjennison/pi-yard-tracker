"""
Database connection and initialization module

Handles SQLite database connection, schema migration, and connection pooling.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = Path("data/detections.db")


class Database:
    """SQLite database connection manager"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection manager
        
        Args:
            db_path: Path to SQLite database file (default: data/detections.db)
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._initialize_schema()
        
        logger.info(f"✅ Database initialized at {self.db_path}")
    
    def _initialize_schema(self):
        """Create database tables if they don't exist"""
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()
        
        logger.info("✅ Database schema initialized")
        
        # Run migrations
        self._run_migrations()
    
    def _run_migrations(self):
        """Run database migrations"""
        try:
            from .migrate import run_migrations
            run_migrations(self.db_path)
        except Exception as e:
            logger.warning(f"⚠️  Migration runner not available or failed: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        
        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM photos")
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            # Return rows as dictionaries
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()):
        """
        Execute a query and return results
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            List of Row objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """
        Execute an INSERT query and return the last row ID
        
        Args:
            query: SQL INSERT query
            params: Query parameters
        
        Returns:
            Last inserted row ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute an UPDATE/DELETE query and return affected rows
        
        Args:
            query: SQL UPDATE/DELETE query
            params: Query parameters
        
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def get_stats(self) -> dict:
        """
        Get database statistics
        
        Returns:
            Dictionary with photo and detection counts
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total photos
            cursor.execute("SELECT COUNT(*) FROM photos")
            total_photos = cursor.fetchone()[0]
            
            # Photos with detections
            cursor.execute("SELECT COUNT(*) FROM photos WHERE has_detections = 1")
            photos_with_detections = cursor.fetchone()[0]
            
            # Total detections
            cursor.execute("SELECT COUNT(*) FROM detections")
            total_detections = cursor.fetchone()[0]
            
            # Detection classes
            cursor.execute("""
                SELECT class_name, COUNT(*) as count 
                FROM detections 
                GROUP BY class_name 
                ORDER BY count DESC
            """)
            classes = [{"class_name": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            # Calculate average detections per photo
            avg_detections_per_photo = (
                total_detections / total_photos if total_photos > 0 else 0.0
            )
            
            # Get unique class count
            unique_classes = len(classes)
            
            # Get most detected class
            most_detected_class = classes[0]["class_name"] if classes else None
            
            # Get latest and oldest photo timestamps
            cursor.execute("SELECT MAX(captured_at) FROM photos")
            latest_photo_time_row = cursor.fetchone()
            latest_photo_time = latest_photo_time_row[0] if latest_photo_time_row[0] else None
            
            cursor.execute("SELECT MIN(captured_at) FROM photos")
            oldest_photo_time_row = cursor.fetchone()
            oldest_photo_time = oldest_photo_time_row[0] if oldest_photo_time_row[0] else None
            
            # Get active session ID (most recent session without an end time)
            cursor.execute("""
                SELECT id FROM detection_sessions 
                WHERE ended_at IS NULL 
                ORDER BY started_at DESC 
                LIMIT 1
            """)
            active_session_row = cursor.fetchone()
            active_session_id = active_session_row[0] if active_session_row else None
            
            return {
                "total_photos": total_photos,
                "photos_with_detections": photos_with_detections,
                "total_detections": total_detections,
                "detection_classes": classes,
                "avg_detections_per_photo": avg_detections_per_photo,
                "unique_classes": unique_classes,
                "most_detected_class": most_detected_class,
                "latest_photo_time": latest_photo_time,
                "oldest_photo_time": oldest_photo_time,
                "active_session_id": active_session_id
            }


# Singleton instance
_db_instance: Optional[Database] = None


def get_db(db_path: Optional[Path] = None) -> Database:
    """
    Get singleton database instance
    
    Args:
        db_path: Optional custom database path
    
    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance
