import sqlite3
import datetime

DB_NAME = 'database.db'

def init_db():
    """Initialize the database with users and recordings tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_note(user_id, text):
    """Save a new note for the user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO recordings (user_id, content) VALUES (?, ?)', (user_id, text))
    conn.commit()
    conn.close()

def get_notes(user_id, limit=5):
    """Retrieve the last N notes for the user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT content, timestamp FROM recordings WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?', (user_id, limit))
    notes = c.fetchall()
    conn.close()
    return notes

def get_all_notes(user_id):
    """Retrieve all notes for the user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT content, timestamp FROM recordings WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    notes = c.fetchall()
    conn.close()
    return notes

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
