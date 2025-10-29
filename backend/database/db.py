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
            classes = [{"class": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            return {
                "total_photos": total_photos,
                "photos_with_detections": photos_with_detections,
                "total_detections": total_detections,
                "detection_classes": classes
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
