"""Tests for feeds module."""

from unittest.mock import MagicMock, patch

from src.feeds import _parse_date, _strip_html, fetch_feed


def _make_mock_feed(entries, title="Test Feed"):
    """Create a mock feedparser result."""
    feed = MagicMock()
    feed.bozo = False
    feed.entries = entries
    feed.feed.title = title
    return feed


def test_strip_html():
    assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"
    assert _strip_html("no tags here") == "no tags here"
    assert _strip_html("<a href='#'>link</a> text") == "link text"


def test_strip_html_whitespace():
    assert _strip_html("<p>  lots   of   spaces  </p>") == "lots of spaces"


@patch("src.feeds.feedparser.parse")
def test_fetch_feed_basic(mock_parse):
    entry = MagicMock()
    entry.get = lambda k, d="": {
        "link": "https://example.com/story1",
        "title": "Test Story",
        "summary": "A test summary",
        "published_parsed": (2026, 2, 18, 10, 0, 0, 0, 0, 0),
    }.get(k, d)

    mock_parse.return_value = _make_mock_feed([entry])
    results = fetch_feed("https://example.com/feed")
    assert len(results) == 1
    assert results[0]["title"] == "Test Story"
    assert results[0]["url"] == "https://example.com/story1"
    assert results[0]["source"] == "Test Feed"


@patch("src.feeds.feedparser.parse")
def test_fetch_feed_skips_entries_without_link(mock_parse):
    entry_no_link = MagicMock()
    entry_no_link.get = lambda k, d="": {
        "title": "No Link",
        "summary": "Missing link",
    }.get(k, d)

    mock_parse.return_value = _make_mock_feed([entry_no_link])
    results = fetch_feed("https://example.com/feed")
    assert len(results) == 0


@patch("src.feeds.feedparser.parse")
def test_fetch_feed_handles_bozo(mock_parse):
    feed = MagicMock()
    feed.bozo = True
    feed.entries = []
    feed.bozo_exception = Exception("parse error")
    mock_parse.return_value = feed

    results = fetch_feed("https://example.com/feed")
    assert results == []


@patch("src.feeds.feedparser.parse")
def test_fetch_feed_handles_exception(mock_parse):
    mock_parse.side_effect = Exception("network error")
    results = fetch_feed("https://example.com/feed")
    assert results == []
