import sqlite3
import json
import uuid
from pathlib import Path

DB_PATH = Path("medagentic.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Original timeline table (kept for backwards compatibility/simplicity if used)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline (
                thread_id TEXT,
                symptom TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # New chat sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # New chat messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                citations TEXT,
                disclaimer TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
            )
        """)
        
        # Need to turn on foreign keys for sqlite
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()

# --- TIMELINE FUNCTIONS ---
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

# --- SESSION FUNCTIONS ---
def create_session(user_email: str, name: str = "New Chat") -> str:
    session_id = str(uuid.uuid4())
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (id, user_email, name) VALUES (?, ?, ?)",
            (session_id, user_email, name)
        )
        conn.commit()
    return session_id

def get_user_sessions(user_email: str) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM sessions WHERE user_email = ? ORDER BY created_at DESC", 
            (user_email,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def rename_session(session_id: str, new_name: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET name = ? WHERE id = ?", (new_name, session_id))
        conn.commit()

def delete_session(session_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()

# --- MESSAGE FUNCTIONS ---
def add_message(session_id: str, role: str, content: str, citations: list = None, disclaimer: str = None) -> str:
    msg_id = str(uuid.uuid4())
    citations_json = json.dumps(citations) if citations else None
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO chat_messages (id, session_id, role, content, citations, disclaimer) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (msg_id, session_id, role, content, citations_json, disclaimer)
        )
        conn.commit()
    return msg_id

def get_session_messages(session_id: str) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,)
        )
        rows = cursor.fetchall()
        
        messages = []
        for r in rows:
            msg = {
                "id": r["id"],
                "role": r["role"],
                "content": r["content"],
                "created_at": r["created_at"]
            }
            if r["citations"]:
                msg["citations"] = json.loads(r["citations"])
            if r["disclaimer"]:
                msg["disclaimer"] = r["disclaimer"]
            messages.append(msg)
        return messages

def get_message_by_id(msg_id: str) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_messages WHERE id = ?", (msg_id,))
        row = cursor.fetchone()
        if not row: return None
        return dict(row)

def delete_messages_after(session_id: str, timestamp: str):
    """Used for rewinding a conversation back to a specific point."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM chat_messages WHERE session_id = ? AND created_at >= ?",
            (session_id, timestamp)
        )
        conn.commit()

init_db()
