"""Database tables and the small helper functions that read and write them (SQLite)."""
import json
import sqlite3
from contextlib import contextmanager

from app.config import settings


@contextmanager
def get_db():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                planner TEXT NOT NULL,
                budget REAL NOT NULL,
                request_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


# ---------- users ----------
def create_user(username: str, email: str, password_hash: str) -> int:
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email.lower(), password_hash),
        )
        return cur.lastrowid


def get_user_by_id(user_id: int):
    with get_db() as db:
        return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_login(login: str):
    """Find a user by username or email."""
    with get_db() as db:
        return db.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?", (login, login)
        ).fetchone()


def username_or_email_taken(username: str, email: str) -> str | None:
    with get_db() as db:
        if db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            return "That username is already taken."
        if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            return "An account with that email already exists."
    return None


# ---------- history ----------
def save_history(user_id: int, planner: str, budget: float, request_data: dict, result: dict) -> int:
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO history (user_id, planner, budget, request_json, result_json) VALUES (?, ?, ?, ?, ?)",
            (user_id, planner, budget, json.dumps(request_data), json.dumps(result)),
        )
        return cur.lastrowid


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "planner": row["planner"],
        "budget": row["budget"],
        "created_at": row["created_at"],
        "request": json.loads(row["request_json"]),
        "result": json.loads(row["result_json"]),
    }


def list_history(user_id: int, limit: int = 50) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_history(user_id: int, history_id: int) -> dict | None:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM history WHERE id = ? AND user_id = ?", (history_id, user_id)
        ).fetchone()
    return _row_to_dict(row) if row else None
