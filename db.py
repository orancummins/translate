"""SQLite persistence for practice-call sessions and their messages."""

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "conversations.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    title TEXT NOT NULL,
    language TEXT NOT NULL,
    locale TEXT NOT NULL,
    locale_label TEXT NOT NULL,
    hotel_type_id TEXT NOT NULL,
    hotel_type_label TEXT NOT NULL,
    persona_id TEXT NOT NULL,
    persona_label TEXT NOT NULL,
    difficulty_id TEXT NOT NULL,
    hotel_name TEXT NOT NULL,
    manager_name TEXT NOT NULL,
    scenario_brief TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    translation TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
"""


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def create_session(*, language, locale, locale_label, hotel_type_id, hotel_type_label,
                    persona_id, persona_label, difficulty_id, hotel_name, manager_name,
                    scenario_brief):
    session_id = uuid.uuid4().hex[:12]
    title = f"{hotel_name} — {persona_label}"
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO sessions
               (id, created_at, title, language, locale, locale_label, hotel_type_id,
                hotel_type_label, persona_id, persona_label, difficulty_id, hotel_name,
                manager_name, scenario_brief)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, now_iso(), title, language, locale, locale_label, hotel_type_id,
             hotel_type_label, persona_id, persona_label, difficulty_id, hotel_name,
             manager_name, scenario_brief),
        )
    return session_id


def list_sessions():
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT s.*,
                      (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) AS message_count
               FROM sessions s
               ORDER BY s.created_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]


def get_session(session_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None


def delete_session(session_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


def add_message(session_id, role, text, translation=None):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO messages (session_id, role, text, translation, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, role, text, translation, now_iso()),
        )
        return cur.lastrowid


def get_messages(session_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def set_translation(message_id, translation):
    with get_conn() as conn:
        conn.execute(
            "UPDATE messages SET translation = ? WHERE id = ?",
            (translation, message_id),
        )


def get_message(message_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
        return dict(row) if row else None
