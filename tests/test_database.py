"""Tests for database module."""

import os
import tempfile

import pytest

os.environ["DB_PATH"] = os.path.join(tempfile.gettempdir(), "test_entertainment.db")

from src.database import (
    cleanup_old_stories,
    get_connection,
    get_sent_hashes,
    init_db,
    is_story_sent,
    log_run,
    mark_stories_sent,
    url_hash,
)


@pytest.fixture(autouse=True)
def fresh_db():
    """Create a fresh database for each test."""
    db_path = os.environ["DB_PATH"]
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()
    yield
    if os.path.exists(db_path):
        os.remove(db_path)


def test_init_db_creates_tables():
    conn = get_connection()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()
    names = [t["name"] for t in tables]
    assert "sent_stories" in names
    assert "runs" in names


def test_url_hash_deterministic():
    h1 = url_hash("https://example.com/story1")
    h2 = url_hash("https://example.com/story1")
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_url_hash_strips_whitespace():
    h1 = url_hash("https://example.com/story1")
    h2 = url_hash("  https://example.com/story1  ")
    assert h1 == h2


def test_mark_and_check_stories():
    stories = [
        {"url": "https://example.com/1", "title": "Story 1", "category": "General"},
        {"url": "https://example.com/2", "title": "Story 2", "category": "Music"},
    ]
    count = mark_stories_sent(stories)
    assert count == 2
    assert is_story_sent("https://example.com/1")
    assert is_story_sent("https://example.com/2")
    assert not is_story_sent("https://example.com/3")


def test_mark_duplicate_stories():
    stories = [{"url": "https://example.com/1", "title": "Story 1", "category": "General"}]
    mark_stories_sent(stories)
    count = mark_stories_sent(stories)  # duplicate
    assert count == 0


def test_get_sent_hashes():
    stories = [
        {"url": "https://example.com/1", "title": "S1", "category": "A"},
        {"url": "https://example.com/2", "title": "S2", "category": "B"},
    ]
    mark_stories_sent(stories)
    hashes = get_sent_hashes()
    assert len(hashes) == 2
    assert url_hash("https://example.com/1") in hashes


def test_log_run():
    log_run(5, '{"General": 3, "Music": 2}', "success")
    conn = get_connection()
    row = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    assert row["stories_sent"] == 5
    assert row["status"] == "success"


def test_cleanup_old_stories():
    stories = [{"url": "https://example.com/old", "title": "Old", "category": "A"}]
    mark_stories_sent(stories)
    # Manually backdate the story
    conn = get_connection()
    conn.execute("UPDATE sent_stories SET sent_at = datetime('now', '-60 days')")
    conn.commit()
    conn.close()
    deleted = cleanup_old_stories()
    assert deleted == 1
    assert not is_story_sent("https://example.com/old")
