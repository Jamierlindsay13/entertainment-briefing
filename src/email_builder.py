"""Jinja2 HTML email rendering."""

import logging
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from config import CATEGORIES, EMAIL_SUBJECT_PREFIX

logger = logging.getLogger(__name__)

CATEGORY_ICONS = {
    "General Entertainment": "&#127916;",  # movie camera
    "Actors & Celebrity": "&#11088;",       # star
    "Musicians & Music": "&#127925;",       # music note
    "Classic Rock": "&#127928;",            # guitar
}


def _get_template_env() -> Environment:
    """Create Jinja2 environment with template directory."""
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    return Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=False,
    )


def render_newsletter(categorized: dict[str, list[dict]], errors: list[str] = None) -> str:
    """Render the newsletter HTML from categorized stories.

    Args:
        categorized: dict mapping category name to list of story dicts
        errors: list of error messages from failed feeds

    Returns:
        Rendered HTML string
    """
    env = _get_template_env()
    template = env.get_template("newsletter.html")

    total_stories = sum(len(stories) for stories in categorized.values())
    category_counts = {cat: len(categorized.get(cat, [])) for cat in CATEGORIES}
    category_count = sum(1 for c in category_counts.values() if c > 0)
    now = datetime.now()

    html = template.render(
        date=now.strftime("%B %d, %Y"),
        generated_at=now.strftime("%Y-%m-%d %H:%M:%S"),
        total_stories=total_stories,
        category_count=category_count,
        category_counts=category_counts,
        categories=categorized,
        category_icons=CATEGORY_ICONS,
        errors=errors or [],
    )

    logger.info(f"Rendered newsletter: {total_stories} stories, {len(html)} bytes")
    return html


def get_email_subject() -> str:
    """Generate email subject line with date."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"{EMAIL_SUBJECT_PREFIX} {date_str}"
