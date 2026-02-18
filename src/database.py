"""SQLite database for dedup tracking and run history."""

import hashlib
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone

from config import DB_FILE, DEDUP_RETENTION_DAYS

logger = logging.getLogger(__name__)


def get_db_path() -> str:
    """Return path to database file."""
    return os.environ.get("DB_PATH", DB_FILE)


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sent_stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                sent_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_sent_stories_hash
                ON sent_stories(url_hash);

            CREATE INDEX IF NOT EXISTS idx_sent_stories_sent_at
                ON sent_stories(sent_at);

            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT NOT NULL DEFAULT (datetime('now')),
                stories_sent INTEGER NOT NULL DEFAULT 0,
                categories_json TEXT,
                status TEXT NOT NULL DEFAULT 'success',
                error_message TEXT
            );
        """)
        conn.commit()
        logger.info(f"Database initialized: {get_db_path()}")
    finally:
        conn.close()


def url_hash(url: str) -> str:
    """Generate SHA-256 hash of a URL for dedup."""
    return hashlib.sha256(url.strip().encode()).hexdigest()


def is_story_sent(url: str) -> bool:
    """Check if a story URL has already been sent."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM sent_stories WHERE url_hash = ?",
            (url_hash(url),),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def get_sent_hashes() -> set[str]:
    """Return set of all sent URL hashes (for batch dedup)."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT url_hash FROM sent_stories").fetchall()
        return {row["url_hash"] for row in rows}
    finally:
        conn.close()


def mark_stories_sent(stories: list[dict]) -> int:
    """Mark a batch of stories as sent. Returns count inserted."""
    if not stories:
        return 0
    conn = get_connection()
    try:
        count = 0
        for story in stories:
            h = url_hash(story["url"])
            try:
                conn.execute(
                    "INSERT INTO sent_stories (url_hash, url, title, category) VALUES (?, ?, ?, ?)",
                    (h, story["url"], story["title"], story.get("category", "")),
                )
                count += 1
            except sqlite3.IntegrityError:
                pass  # already exists
        conn.commit()
        logger.info(f"Marked {count} stories as sent")
        return count
    finally:
        conn.close()


def log_run(stories_sent: int, categories_json: str = "", status: str = "success", error_message: str = "") -> None:
    """Log a run to the runs table."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO runs (stories_sent, categories_json, status, error_message) VALUES (?, ?, ?, ?)",
            (stories_sent, categories_json, status, error_message),
        )
        conn.commit()
    finally:
        conn.close()


def cleanup_old_stories() -> int:
    """Delete stories older than retention period. Returns count deleted."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=DEDUP_RETENTION_DAYS)).isoformat()
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM sent_stories WHERE sent_at < ?", (cutoff,)
        )
        conn.commit()
        deleted = cursor.rowcount
        if deleted:
            logger.info(f"Cleaned up {deleted} stories older than {DEDUP_RETENTION_DAYS} days")
        return deleted
    finally:
        conn.close()
