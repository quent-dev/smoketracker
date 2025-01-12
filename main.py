import sqlite3
import database


# Create an instance of DatabaseManager
db = DatabaseManager()

# Example usage with the context manager
with db.get_connection() as conn:
    # Execute your queries here
    cursor = conn.execute("SELECT * FROM settings")
    settings = cursor.fetchall()
