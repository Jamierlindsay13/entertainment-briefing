"""Entertainment Briefing CLI: init-db | generate | preview | send [--dry-run]"""

import argparse
import json
import logging
import os
import sys
import webbrowser
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    ACTORS_CELEBRITY_FEEDS,
    CLASSIC_ROCK_FEEDS,
    GENERAL_ENTERTAINMENT_FEEDS,
    MIN_TOTAL_STORIES,
    MUSICIANS_MUSIC_FEEDS,
)
from src.database import cleanup_old_stories, init_db, log_run, mark_stories_sent
from src.email_builder import get_email_subject, render_newsletter
from src.feeds import fetch_feeds
from src.filters import process_all_stories
from src.notifications import send_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _collect_stories() -> tuple[dict, list[str]]:
    """Fetch all feeds, categorize and dedup.

    Returns (categorized_stories, errors).
    """
    errors = []

    logger.info("Fetching General Entertainment feeds...")
    general_stories = fetch_feeds(GENERAL_ENTERTAINMENT_FEEDS)
    if not general_stories:
        errors.append("General Entertainment feeds")

    logger.info("Fetching Actors & Celebrity feeds...")
    actor_stories = fetch_feeds(ACTORS_CELEBRITY_FEEDS)
    if not actor_stories:
        errors.append("Actors & Celebrity feeds")

    logger.info("Fetching Musicians & Music feeds...")
    music_stories = fetch_feeds(MUSICIANS_MUSIC_FEEDS)
    if not music_stories:
        errors.append("Musicians & Music feeds")

    logger.info("Fetching Classic Rock feeds...")
    classic_rock_stories = fetch_feeds(CLASSIC_ROCK_FEEDS)
    if not classic_rock_stories:
        errors.append("Classic Rock feeds")

    logger.info("Processing stories...")
    categorized = process_all_stories(
        general_stories, actor_stories, music_stories,
        classic_rock_stories,
    )

    return categorized, errors


def cmd_init_db(args):
    """Initialize the database."""
    init_db()
    logger.info("Database initialized successfully")


def cmd_generate(args):
    """Generate briefing HTML and write to file."""
    categorized, errors = _collect_stories()

    total = sum(len(s) for s in categorized.values())
    if total == 0:
        logger.error("No stories collected, aborting")
        sys.exit(1)

    html = render_newsletter(categorized, errors)

    os.makedirs("output", exist_ok=True)
    filename = f"output/briefing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"Briefing saved to {filename} ({total} stories)")
    return html, filename, categorized


def cmd_preview(args):
    """Generate and open briefing in browser."""
    html, filename, _ = cmd_generate(args)
    filepath = os.path.abspath(filename)
    logger.info(f"Opening {filepath} in browser...")
    webbrowser.open(f"file://{filepath}")


def cmd_send(args):
    """Generate and send briefing via email."""
    to_email = os.environ.get("NOTIFICATION_EMAIL")
    if not to_email:
        logger.error("NOTIFICATION_EMAIL not set")
        sys.exit(1)

    # Initialize DB if needed
    init_db()

    # Cleanup old stories
    cleanup_old_stories()

    categorized, errors = _collect_stories()

    total = sum(len(s) for s in categorized.values())
    if total < MIN_TOTAL_STORIES:
        msg = f"Only {total} stories collected (minimum {MIN_TOTAL_STORIES}), skipping send"
        logger.warning(msg)
        log_run(total, json.dumps({c: len(s) for c, s in categorized.items()}), "skipped", msg)
        return

    html = render_newsletter(categorized, errors)
    subject = get_email_subject()

    if args.dry_run:
        logger.info(f"[DRY RUN] Would send {len(html)} bytes to {to_email}: {subject}")
        logger.info(f"[DRY RUN] Categories: {json.dumps({c: len(s) for c, s in categorized.items()})}")
        smtp_email = os.environ.get("SMTP_EMAIL")
        smtp_pass = os.environ.get("SMTP_PASSWORD")
        if smtp_email and smtp_pass:
            logger.info(f"[DRY RUN] SMTP credentials present ({smtp_email})")
        else:
            logger.warning("[DRY RUN] SMTP credentials missing")
        return

    success = send_email(to_email, subject, html)

    if success:
        # Mark all stories as sent
        all_stories = []
        for stories in categorized.values():
            all_stories.extend(stories)
        mark_stories_sent(all_stories)
        log_run(total, json.dumps({c: len(s) for c, s in categorized.items()}))
        logger.info(f"Briefing sent successfully ({total} stories)")
    else:
        log_run(total, json.dumps({c: len(s) for c, s in categorized.items()}), "failed", "SMTP send failed")
        logger.error("Failed to send briefing")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Daily Entertainment Briefing Generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init-db
    init_parser = subparsers.add_parser("init-db", help="Initialize SQLite database")
    init_parser.set_defaults(func=cmd_init_db)

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate briefing HTML to file")
    gen_parser.set_defaults(func=cmd_generate)

    # preview
    prev_parser = subparsers.add_parser("preview", help="Generate and open in browser")
    prev_parser.set_defaults(func=cmd_preview)

    # send
    send_parser = subparsers.add_parser("send", help="Generate and send via email")
    send_parser.add_argument("--dry-run", action="store_true", help="Verify config without sending")
    send_parser.set_defaults(func=cmd_send)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
