import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str = "smoking_tracker.db"):
        """Initialize the database manager with the database file path."""
        self.db_path = db_path
        self.initialize_database()
        self.initialize_default_settings()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON")
        # Return dictionary-like objects instead of tuples
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def initialize_database(self):
        """Create database tables if they don't exist."""
        create_tables_sql = """
        -- Cigarettes table
        CREATE TABLE IF NOT EXISTS cigarettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            trigger_category TEXT,
            location TEXT
        );

        -- Daily Stats table
        CREATE TABLE IF NOT EXISTS daily_stats (
            date DATE PRIMARY KEY,
            total_count INTEGER DEFAULT 0,
            target_goal INTEGER,
            money_spent REAL,
            success_rating INTEGER CHECK(success_rating BETWEEN 1 AND 5)
        );

        -- Goals table
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date DATE DEFAULT CURRENT_DATE,
            goal_type TEXT NOT NULL,
            target_value INTEGER,
            achieved BOOLEAN DEFAULT 0,
            achieved_date DATE
        );

        -- Settings table
        CREATE TABLE IF NOT EXISTS settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_cigarettes_timestamp ON cigarettes(timestamp);
        CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date);
        """

        with self.get_connection() as conn:
            conn.executescript(create_tables_sql)

    def get_db_version(self) -> Optional[str]:
        """Get the database version from settings."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT setting_value FROM settings WHERE setting_key = 'db_version'"
            )
            result = cursor.fetchone()
            return result['setting_value'] if result else None

    def initialize_default_settings(self):
        """Initialize default settings in the database."""
        default_settings = [
            ('db_version', '1.0'),
            ('cigarettes_per_pack', '20'),
            ('price_per_pack', '4.25'),
            ('daily_limit', '20'),
        ]
        
        with self.get_connection() as conn:
            conn.executemany(
                """INSERT OR REPLACE INTO settings (setting_key, setting_value)
                   VALUES (?, ?)""",
                default_settings
            )
