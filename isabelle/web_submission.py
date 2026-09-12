"""Creating events from events.hackclub.com rather than the Slack modal.

The Slack modal collects a rich_text_input, so create_event expects Slack's
rich text structure alongside the rendered markdown. A web form has no such
thing, but RawDescription cannot simply be left empty: get_edit_event_modal and
the app home both json.loads it, and the edit modal pre-fills its description
from it, so an empty value would show a blank description and wipe it on save.

Synthesising a single rich_text_section from the submitted text keeps every
existing reader working and round-trips back through rich_text_to_md unchanged.
The tradeoff is that markdown syntax shows literally inside Slack.
"""

from datetime import datetime
from datetime import timezone

DEFAULT_EVENT_LINK = "https://app.slack.com/huddle/T0266FRGM/C01D7AHKMPF"

MAX_TITLE = 120
MAX_DESCRIPTION = 4000
MAX_DURATION = 24 * 60 * 60


def as_rich_text(description: str) -> list[dict]:
    return [
        {
            "type": "rich_text_section",
            "elements": [{"type": "text", "text": description}],
        }
    ]


def parse_timestamp(value):
    """Isabelle stores naive UTC; events.hackclub.com appends 'Z' when reading
    it back. Anything offset-aware has to be normalised or the site would
    re-label an already-local time as UTC."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def validate(body: dict, allowed_tags: list[str]) -> tuple[dict, dict]:
    """Returns (errors, values). Mirrors the checks the web form makes, because
    the form cannot be trusted to have made them."""
    errors: dict[str, str] = {}

    title = (body.get("title") or "").strip()
    if not title:
        errors["title"] = "title is required"
    elif len(title) > MAX_TITLE:
        errors["title"] = f"title must be under {MAX_TITLE} characters"

    description = (body.get("description") or "").strip()
    if not description:
        errors["description"] = "description is required"
    elif len(description) > MAX_DESCRIPTION:
        errors["description"] = (
            f"description must be under {MAX_DESCRIPTION} characters"
        )

    start = parse_timestamp(body.get("start_time"))
    end = parse_timestamp(body.get("end_time"))

    if start is None:
        errors["start_time"] = "start_time must be an ISO 8601 timestamp"
    if end is None:
        errors["end_time"] = "end_time must be an ISO 8601 timestamp"
    elif start is not None:
        if end <= start:
            errors["end_time"] = "end_time must be after start_time"
        elif (end - start).total_seconds() > MAX_DURATION:
            errors["end_time"] = "events cannot run longer than 24 hours"

    leader_slack_id = (body.get("leader_slack_id") or "").strip()
    if not leader_slack_id:
        errors["leader_slack_id"] = "leader_slack_id is required"

    event_link = (body.get("event_link") or "").strip() or DEFAULT_EVENT_LINK
    rsvp_form_url = (body.get("rsvp_form_url") or "").strip() or None

    for field, value in (("event_link", event_link), ("rsvp_form_url", rsvp_form_url)):
        if value and not value.startswith("https://"):
            errors[field] = f"{field} must be an https:// URL"

    raw_tags = body.get("tags")
    tags = (
        [t for t in raw_tags if t in allowed_tags]
        if isinstance(raw_tags, list)
        else []
    )

    return errors, {
        "title": title,
        "description": description,
        "start_time": start,
        "end_time": end,
        "leader_slack_id": leader_slack_id,
        "event_link": event_link,
        "rsvp_form_url": rsvp_form_url,
        "tags": tags,
    }
