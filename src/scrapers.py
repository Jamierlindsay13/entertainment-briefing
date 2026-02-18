"""Edmonton events scraping: Ticketmaster Discovery API."""

import logging
import os
from datetime import datetime, timedelta, timezone

import requests

from config import (
    EDMONTON_LATLONG,
    EDMONTON_RADIUS,
    TICKETMASTER_BASE_URL,
    TICKETMASTER_PAGE_SIZE,
)

logger = logging.getLogger(__name__)


def fetch_edmonton_events() -> list[dict]:
    """Fetch upcoming Edmonton events from Ticketmaster Discovery API.

    Returns list of dicts with keys: title, url, published, summary, source, venue, date.
    Returns empty list if TICKETMASTER_API_KEY is not set.
    """
    api_key = os.environ.get("TICKETMASTER_API_KEY")
    if not api_key:
        logger.info("TICKETMASTER_API_KEY not set, skipping Edmonton events")
        return []

    try:
        events = _fetch_ticketmaster_events(api_key)
        logger.info(f"Fetched {len(events)} Edmonton events from Ticketmaster")
        return events
    except Exception as e:
        logger.error(f"Failed to fetch Edmonton events: {e}")
        return []


def _fetch_ticketmaster_events(api_key: str) -> list[dict]:
    """Query Ticketmaster Discovery API for Edmonton area events."""
    now = datetime.now(timezone.utc)
    start_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = (now + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    lat, lng = EDMONTON_LATLONG.split(",")

    params = {
        "apikey": api_key,
        "latlong": f"{lat},{lng}",
        "radius": EDMONTON_RADIUS,
        "unit": "km",
        "size": TICKETMASTER_PAGE_SIZE,
        "sort": "date,asc",
        "startDateTime": start_date,
        "endDateTime": end_date,
        "classificationName": "Music,Film,Arts & Theatre,Comedy",
    }

    resp = requests.get(
        f"{TICKETMASTER_BASE_URL}/events.json",
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    embedded = data.get("_embedded", {})
    raw_events = embedded.get("events", [])

    events = []
    seen_names = set()

    for event in raw_events:
        name = event.get("name", "").strip()
        if not name or name.lower() in seen_names:
            continue
        seen_names.add(name.lower())

        url = event.get("url", "")
        venue_name = ""
        venues = event.get("_embedded", {}).get("venues", [])
        if venues:
            venue_name = venues[0].get("name", "")

        event_date = ""
        dates = event.get("dates", {}).get("start", {})
        event_date = dates.get("localDate", "")
        event_time = dates.get("localTime", "")
        if event_date and event_time:
            event_date = f"{event_date} {event_time}"

        # Build summary
        classifications = event.get("classifications", [])
        genre = ""
        if classifications:
            genre = classifications[0].get("genre", {}).get("name", "")

        summary_parts = []
        if venue_name:
            summary_parts.append(f"at {venue_name}")
        if event_date:
            summary_parts.append(f"on {event_date}")
        if genre and genre != "Undefined":
            summary_parts.append(f"({genre})")
        summary = " ".join(summary_parts)

        events.append({
            "title": name,
            "url": url,
            "published": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "source": "Ticketmaster",
            "venue": venue_name,
            "date": event_date,
        })

    return events
