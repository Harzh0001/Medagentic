import sqlite3
import json
from pathlib import Path

DB_PATH = Path("medagentic.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline (
                thread_id TEXT,
                symptom TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def add_symptom(thread_id: str, symptom: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO timeline (thread_id, symptom) VALUES (?, ?)", (thread_id, symptom))
        conn.commit()

def get_timeline(thread_id: str) -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT symptom, timestamp FROM timeline WHERE thread_id = ? ORDER BY timestamp ASC", (thread_id,))
        rows = cursor.fetchall()
        return [f"[{row[1]}] {row[0]}" for row in rows]

init_db()
