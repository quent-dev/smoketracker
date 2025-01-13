from datetime import datetime, date
from typing import List, Optional, Dict
import sqlite3

class CigaretteTracker:
    def __init__(self, db_manager):
        """Initialize the cigarette tracker with a database manager instance."""
        self.db = db_manager

    def add_cigarette(self, notes: Optional[str] = None, 
                     trigger_category: Optional[str] = None,
                     location: Optional[str] = None) -> int:
        """
        Record a new cigarette entry.
        Returns the ID of the new entry.
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO cigarettes (timestamp, notes, trigger_category, location)
                VALUES (CURRENT_TIMESTAMP, ?, ?, ?)
                """, (notes, trigger_category, location))
            
            # Update daily stats
            today = date.today()
            conn.execute("""
                INSERT INTO daily_stats (date, total_count)
                VALUES (?, 1)
                ON CONFLICT(date) DO UPDATE SET
                total_count = total_count + 1
                """, (today,))
            
            return cursor.lastrowid

    def get_cigarette(self, cigarette_id: int) -> Optional[Dict]:
        """Retrieve a specific cigarette entry by ID."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, timestamp, notes, trigger_category, location
                FROM cigarettes
                WHERE id = ?
                """, (cigarette_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_cigarette(self, cigarette_id: int, 
                        notes: Optional[str] = None,
                        trigger_category: Optional[str] = None,
                        location: Optional[str] = None) -> bool:
        """
        Update an existing cigarette entry.
        Returns True if successful, False if entry not found.
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE cigarettes
                SET notes = COALESCE(?, notes),
                    trigger_category = COALESCE(?, trigger_category),
                    location = COALESCE(?, location)
                WHERE id = ?
                """, (notes, trigger_category, location, cigarette_id))
            return cursor.rowcount > 0

    def delete_cigarette(self, cigarette_id: int) -> bool:
        """
        Delete a cigarette entry and update daily stats.
        Returns True if successful, False if entry not found.
        """
        with self.db.get_connection() as conn:
            # Get the date of the cigarette first
            cursor = conn.execute("""
                SELECT date(timestamp) as smoke_date
                FROM cigarettes
                WHERE id = ?
                """, (cigarette_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
                
            smoke_date = row['smoke_date']
            
            # Delete the cigarette
            conn.execute("DELETE FROM cigarettes WHERE id = ?", (cigarette_id,))
            
            # Update daily stats
            conn.execute("""
                UPDATE daily_stats
                SET total_count = total_count - 1
                WHERE date = ? AND total_count > 0
                """, (smoke_date,))
            
            return True

    def get_daily_cigarettes(self, day: date = None) -> List[Dict]:
        """Get all cigarettes for a specific day."""
        if day is None:
            day = date.today()
        print(f"Fetching cigarettes for date: {day}")
        
        with self.db.get_connection() as conn:
            # Debug: Check what's in the cigarettes table
            cursor = conn.execute("SELECT COUNT(*) as count FROM cigarettes")
            total_count = cursor.fetchone()['count']
            print(f"Total cigarettes in database: {total_count}")
            
            # Debug: Show a sample of raw timestamps
            cursor = conn.execute("""
                SELECT timestamp, date(timestamp, 'localtime') as formatted_date 
                FROM cigarettes 
                LIMIT 3""")
            samples = cursor.fetchall()
            print("Sample timestamps from DB:")
            for sample in samples:
                print(f"Raw timestamp: {sample['timestamp']}, Formatted date: {sample['formatted_date']}")
            
            # Original query with parameter logging
            query = """
                SELECT id, timestamp, notes, trigger_category, location
                FROM cigarettes
                WHERE date(timestamp, 'localtime') = ?
                ORDER BY timestamp DESC
            """
            print(f"Executing query: {query}")
            print(f"With parameter: {day.isoformat()}")
            
            cursor = conn.execute(query, (day.isoformat(),))
            results = [dict(row) for row in cursor.fetchall()]
            print(f"Query returned {len(results)} results")
            return results

    def get_stats_for_day(self, day: date = None) -> Dict:
        """Get statistics for a specific day."""
        if day is None:
            day = date.today()

        with self.db.get_connection() as conn:
            # Get daily stats
            cursor = conn.execute("""
                SELECT total_count, target_goal, money_spent, success_rating
                FROM daily_stats
                WHERE date = ?
                """, (day,))
            stats = dict(cursor.fetchone() or {})
            
            # Get time patterns
            cursor = conn.execute("""
                SELECT 
                    strftime('%H', timestamp) as hour,
                    COUNT(*) as count
                FROM cigarettes
                WHERE date(timestamp) = ?
                GROUP BY hour
                ORDER BY hour
                """, (day,))
            stats['hourly_breakdown'] = {row['hour']: row['count'] for row in cursor}
            
            # Get triggers breakdown
            cursor = conn.execute("""
                SELECT 
                    COALESCE(trigger_category, 'unknown') as trigger,
                    COUNT(*) as count
                FROM cigarettes
                WHERE date(timestamp) = ?
                GROUP BY trigger_category
                """, (day,))
            stats['triggers'] = {row['trigger']: row['count'] for row in cursor}
            
            return stats
