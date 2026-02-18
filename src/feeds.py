"""RSS feed fetching and normalization."""

import logging
import time
from datetime import datetime, timezone

import feedparser

from config import FEED_DELAY, FEED_TIMEOUT, USER_AGENT

logger = logging.getLogger(__name__)


def fetch_feed(url: str) -> list[dict]:
    """Fetch and normalize entries from a single RSS feed.

    Returns list of dicts with keys: title, url, published, summary, source.
    """
    try:
        feed = feedparser.parse(
            url,
            agent=USER_AGENT,
            request_headers={"Accept": "application/rss+xml, application/xml, text/xml"},
        )

        if feed.bozo and not feed.entries:
            logger.warning(f"Feed error for {url}: {feed.bozo_exception}")
            return []

        source = _extract_source(feed, url)
        entries = []

        for entry in feed.entries:
            link = entry.get("link", "")
            title = entry.get("title", "").strip()
            if not link or not title:
                continue

            published = _parse_date(entry)
            summary = entry.get("summary", entry.get("description", ""))
            # Strip HTML tags from summary
            if summary:
                summary = _strip_html(summary)[:500]

            entries.append({
                "title": title,
                "url": link,
                "published": published,
                "summary": summary,
                "source": source,
            })

        logger.info(f"Fetched {len(entries)} entries from {source} ({url})")
        return entries

    except Exception as e:
        logger.error(f"Failed to fetch feed {url}: {e}")
        return []


def fetch_feeds(urls: list[str]) -> list[dict]:
    """Fetch multiple RSS feeds with rate limiting.

    Returns combined list of normalized entries.
    """
    all_entries = []
    for i, url in enumerate(urls):
        entries = fetch_feed(url)
        all_entries.extend(entries)
        if i < len(urls) - 1:
            time.sleep(FEED_DELAY)
    return all_entries


def _extract_source(feed: feedparser.FeedParserDict, url: str) -> str:
    """Extract a human-readable source name from feed metadata or URL."""
    if hasattr(feed, "feed") and hasattr(feed.feed, "title") and feed.feed.title:
        return feed.feed.title.strip()
    # Fallback: extract domain
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url


def _parse_date(entry) -> str:
    """Parse published date from feed entry, return ISO format string."""
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                dt = datetime(*parsed[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except Exception:
                pass
    for field in ("published", "updated"):
        raw = entry.get(field)
        if raw:
            return raw
    return datetime.now(timezone.utc).isoformat()


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean
