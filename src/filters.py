"""Story categorization, keyword matching, and deduplication."""

import logging
from datetime import datetime, timezone

from config import (
    ACTOR_KEYWORDS,
    ACTORS_CELEBRITY_FEEDS,
    ACTORS_CROSS_FILTER_FEEDS,
    CATEGORIES,
    CLASSIC_ROCK_CROSS_FILTER_FEEDS,
    CLASSIC_ROCK_FEEDS,
    CLASSIC_ROCK_KEYWORDS,
    GENERAL_ENTERTAINMENT_FEEDS,
    MUSICIANS_MUSIC_FEEDS,
    STORIES_PER_CATEGORY,
)
from src.database import get_sent_hashes, url_hash

logger = logging.getLogger(__name__)


def _feed_url_matches(story_source_url: str, feed_urls: list[str]) -> bool:
    """Check if a story came from one of the given feed URLs (by domain match)."""
    from urllib.parse import urlparse

    try:
        story_domain = urlparse(story_source_url).netloc.lower().replace("www.", "")
    except Exception:
        return False

    for feed_url in feed_urls:
        try:
            feed_domain = urlparse(feed_url).netloc.lower().replace("www.", "")
            if story_domain == feed_domain:
                return True
        except Exception:
            continue
    return False


def _matches_keywords(story: dict, keywords: list[str]) -> bool:
    """Check if story title or summary matches any keywords (case-insensitive)."""
    text = f"{story.get('title', '')} {story.get('summary', '')}".lower()
    return any(kw.lower() in text for kw in keywords)


def categorize_stories(
    general_stories: list[dict],
    actor_stories: list[dict],
    music_stories: list[dict],
    classic_rock_stories: list[dict],
    edmonton_events: list[dict],
) -> dict[str, list[dict]]:
    """Assign stories to categories with cross-filtering.

    Returns dict mapping category name to list of stories.
    """
    categorized = {cat: [] for cat in CATEGORIES}

    # 1. General Entertainment - direct from feeds
    for story in general_stories:
        story["category"] = "General Entertainment"
        categorized["General Entertainment"].append(story)

    # 2. Actors & Celebrity - direct from Hollywood Reporter + cross-filter
    for story in actor_stories:
        story["category"] = "Actors & Celebrity"
        categorized["Actors & Celebrity"].append(story)

    # Cross-filter: Variety/Deadline stories matching actor keywords
    for story in general_stories:
        if _matches_keywords(story, ACTOR_KEYWORDS):
            cross_story = story.copy()
            cross_story["category"] = "Actors & Celebrity"
            categorized["Actors & Celebrity"].append(cross_story)

    # 3. Musicians & Music - direct from music feeds
    for story in music_stories:
        story["category"] = "Musicians & Music"
        categorized["Musicians & Music"].append(story)

    # 4. Edmonton Events
    for event in edmonton_events:
        event["category"] = "Edmonton Events"
        categorized["Edmonton Events"].append(event)

    # 5. Classic Rock - direct from UCR/Louder + cross-filter
    for story in classic_rock_stories:
        story["category"] = "Classic Rock"
        categorized["Classic Rock"].append(story)

    # Cross-filter: Rolling Stone stories matching classic rock keywords
    for story in music_stories:
        if _matches_keywords(story, CLASSIC_ROCK_KEYWORDS):
            cross_story = story.copy()
            cross_story["category"] = "Classic Rock"
            categorized["Classic Rock"].append(cross_story)

    return categorized


def dedup_stories(categorized: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Remove stories that have already been sent (by URL hash).

    Also deduplicates within categories by URL.
    """
    sent_hashes = get_sent_hashes()
    result = {}

    for category, stories in categorized.items():
        seen_urls = set()
        unique = []
        for story in stories:
            h = url_hash(story["url"])
            if h in sent_hashes:
                continue
            if story["url"] in seen_urls:
                continue
            seen_urls.add(story["url"])
            unique.append(story)
        result[category] = unique

    total_dupes = sum(len(categorized[c]) - len(result[c]) for c in categorized)
    if total_dupes:
        logger.info(f"Dedup removed {total_dupes} stories")

    return result


def sort_and_limit(categorized: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Sort stories by publish date (newest first) and limit per category."""
    result = {}
    for category, stories in categorized.items():
        # Sort by published date, newest first
        sorted_stories = sorted(
            stories,
            key=lambda s: s.get("published", ""),
            reverse=True,
        )
        result[category] = sorted_stories[:STORIES_PER_CATEGORY]
    return result


def process_all_stories(
    general_stories: list[dict],
    actor_stories: list[dict],
    music_stories: list[dict],
    classic_rock_stories: list[dict],
    edmonton_events: list[dict],
) -> dict[str, list[dict]]:
    """Full pipeline: categorize -> dedup -> sort/limit."""
    categorized = categorize_stories(
        general_stories, actor_stories, music_stories,
        classic_rock_stories, edmonton_events,
    )
    deduped = dedup_stories(categorized)
    limited = sort_and_limit(deduped)

    for cat, stories in limited.items():
        logger.info(f"  {cat}: {len(stories)} stories")

    return limited
