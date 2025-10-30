"""
Database migration runner

Applies database migrations in order to update schema.
"""

import logging
import sqlite3
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles database schema migrations"""
    
    def __init__(self, db_path: Path, migrations_dir: Path):
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Create migrations tracking table if it doesn't exist"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()
    
    def _get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.execute("SELECT migration_name FROM schema_migrations ORDER BY id")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def _mark_migration_applied(self, migration_name: str):
        """Mark a migration as applied"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES (?)",
                (migration_name,)
            )
            conn.commit()
        finally:
            conn.close()
    
    def run_migrations(self):
        """Run all pending migrations"""
        if not self.migrations_dir.exists():
            logger.info("📁 No migrations directory found")
            return
        
        # Get migration files
        migration_files = sorted(self.migrations_dir.glob("*.sql"))
        if not migration_files:
            logger.info("📁 No migration files found")
            return
        
        # Get applied migrations
        applied = set(self._get_applied_migrations())
        
        # Apply pending migrations
        for migration_file in migration_files:
            migration_name = migration_file.name
            
            if migration_name in applied:
                logger.debug(f"⏭️  Skipping {migration_name} (already applied)")
                continue
            
            logger.info(f"🔄 Applying migration: {migration_name}")
            
            try:
                # Read migration SQL
                sql = migration_file.read_text()
                
                # Apply migration
                conn = sqlite3.connect(str(self.db_path))
                try:
                    # Split on semicolons and execute each statement
                    for statement in sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            conn.execute(statement)
                    conn.commit()
                    
                    # Mark as applied
                    self._mark_migration_applied(migration_name)
                    logger.info(f"✅ Applied {migration_name}")
                finally:
                    conn.close()
                    
            except Exception as e:
                logger.error(f"❌ Failed to apply {migration_name}: {e}")
                raise


def run_migrations(db_path: Path):
    """
    Run all pending database migrations
    
    Args:
        db_path: Path to SQLite database file
    """
    migrations_dir = Path(__file__).parent / "migrations"
    runner = MigrationRunner(db_path, migrations_dir)
    runner.run_migrations()
