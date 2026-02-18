"""Tests for filters module."""

import os
import tempfile

import pytest

os.environ["DB_PATH"] = os.path.join(tempfile.gettempdir(), "test_filters.db")

from src.database import init_db, mark_stories_sent
from src.filters import (
    _matches_keywords,
    categorize_stories,
    dedup_stories,
    sort_and_limit,
)


@pytest.fixture(autouse=True)
def fresh_db():
    db_path = os.environ["DB_PATH"]
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()
    yield
    if os.path.exists(db_path):
        os.remove(db_path)


def _make_story(title="Test", url="https://example.com/1", summary="", source="test.com", published="2026-02-18T10:00:00"):
    return {"title": title, "url": url, "summary": summary, "source": source, "published": published}


def test_matches_keywords():
    story = _make_story(title="Brad Pitt lands new film role")
    assert _matches_keywords(story, ["film role", "casting"])

    story2 = _make_story(title="New restaurant opens")
    assert not _matches_keywords(story2, ["film role", "casting"])


def test_matches_keywords_case_insensitive():
    story = _make_story(title="LED ZEPPELIN reunion announced")
    assert _matches_keywords(story, ["led zeppelin"])


def test_categorize_stories_basic():
    general = [_make_story("Gen 1", "https://a.com/1"), _make_story("Gen 2", "https://a.com/2")]
    actors = [_make_story("Actor 1", "https://b.com/1")]
    music = [_make_story("Music 1", "https://c.com/1")]
    rock = [_make_story("Rock 1", "https://d.com/1")]

    result = categorize_stories(general, actors, music, rock)
    assert len(result["General Entertainment"]) == 2
    assert len(result["Actors & Celebrity"]) >= 1
    assert len(result["Musicians & Music"]) == 1
    assert len(result["Classic Rock"]) >= 1


def test_categorize_cross_filter_actors_moves_not_copies():
    general = [_make_story("Star lands casting role in new film", "https://variety.com/1")]
    result = categorize_stories(general, [], [], [])
    # Should move to Actors, NOT appear in General
    assert len(result["General Entertainment"]) == 0
    assert len(result["Actors & Celebrity"]) == 1
    assert result["Actors & Celebrity"][0]["title"] == "Star lands casting role in new film"


def test_categorize_cross_filter_classic_rock_moves_not_copies():
    music = [_make_story("Led Zeppelin remaster announced", "https://rollingstone.com/1")]
    result = categorize_stories([], [], music, [])
    # Should move to Classic Rock, NOT appear in Music
    assert len(result["Musicians & Music"]) == 0
    assert len(result["Classic Rock"]) == 1
    assert result["Classic Rock"][0]["title"] == "Led Zeppelin remaster announced"


def test_no_duplicate_urls_across_categories():
    general = [
        _make_story("Oscar winner casting news", "https://variety.com/1"),
        _make_story("Normal entertainment", "https://variety.com/2"),
    ]
    music = [
        _make_story("Led Zeppelin tour", "https://rollingstone.com/1"),
        _make_story("New pop album", "https://rollingstone.com/2"),
    ]
    result = categorize_stories(general, [], music, [])
    all_urls = []
    for stories in result.values():
        all_urls.extend(s["url"] for s in stories)
    assert len(all_urls) == len(set(all_urls)), "Duplicate URLs found across categories"


def test_dedup_removes_sent():
    stories = [_make_story("Sent", "https://a.com/sent")]
    mark_stories_sent(stories)

    categorized = {"General Entertainment": [_make_story("Sent", "https://a.com/sent")]}
    result = dedup_stories(categorized)
    assert len(result["General Entertainment"]) == 0


def test_dedup_removes_within_category():
    categorized = {
        "General Entertainment": [
            _make_story("Same", "https://a.com/1"),
            _make_story("Same Again", "https://a.com/1"),
        ]
    }
    result = dedup_stories(categorized)
    assert len(result["General Entertainment"]) == 1


def test_sort_and_limit():
    stories = [_make_story(f"Story {i}", f"https://a.com/{i}", published=f"2026-02-{18-i:02d}T10:00:00") for i in range(15)]
    categorized = {"General Entertainment": stories}
    result = sort_and_limit(categorized)
    assert len(result["General Entertainment"]) == 10
    # Newest first
    assert result["General Entertainment"][0]["title"] == "Story 0"
