"""Tests for email_builder module."""

from src.email_builder import CATEGORY_ICONS, get_email_subject, render_newsletter


def _make_categorized(n_per_cat=2):
    """Create sample categorized stories."""
    categories = {}
    for cat in ["General Entertainment", "Actors & Celebrity", "Musicians & Music", "Edmonton Events", "Classic Rock"]:
        stories = []
        for i in range(n_per_cat):
            stories.append({
                "title": f"{cat} Story {i+1}",
                "url": f"https://example.com/{cat.lower().replace(' ', '-')}/{i+1}",
                "summary": f"Summary for {cat} story {i+1}",
                "source": "test.com",
                "published": "2026-02-18T10:00:00",
            })
        categories[cat] = stories
    return categories


def test_render_newsletter_basic():
    categorized = _make_categorized()
    html = render_newsletter(categorized)
    assert "Daily Entertainment Briefing" in html
    assert "General Entertainment" in html
    assert "Musicians & Music" in html
    assert "Classic Rock" in html


def test_render_newsletter_includes_stories():
    categorized = _make_categorized()
    html = render_newsletter(categorized)
    assert "General Entertainment Story 1" in html
    assert "https://example.com/general-entertainment/1" in html


def test_render_newsletter_with_errors():
    categorized = _make_categorized()
    html = render_newsletter(categorized, errors=["variety.com", "deadline.com"])
    assert "variety.com" in html
    assert "Some sources were unavailable" in html


def test_render_newsletter_empty_categories():
    categorized = {
        "General Entertainment": [],
        "Actors & Celebrity": [],
        "Musicians & Music": [{"title": "One", "url": "https://a.com/1", "summary": "S", "source": "s", "published": ""}],
        "Edmonton Events": [],
        "Classic Rock": [],
    }
    html = render_newsletter(categorized)
    assert "Musicians & Music" in html
    assert "1 stories" in html or "(1)" in html


def test_get_email_subject():
    subject = get_email_subject()
    assert subject.startswith("[Entertainment Briefing]")
    assert "202" in subject  # contains year


def test_category_icons_all_present():
    for cat in ["General Entertainment", "Actors & Celebrity", "Musicians & Music", "Edmonton Events", "Classic Rock"]:
        assert cat in CATEGORY_ICONS
