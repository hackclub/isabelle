import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Optional

from slack_sdk.web.async_client import AsyncWebClient

from isabelle.tables import DigestState
from isabelle.utils.env import env
from isabelle.utils.utils import rich_text_to_mrkdwn

client = AsyncWebClient(token=env.slack_bot_token)
logger = logging.getLogger(__name__)

# One row, looked up by this key. A digest is a property of the deploy, not of
# any event, so it cannot hang its state off the event rows the way the RSVP
# reminders do.
STATE_KEY = "event_digest"

# Slack refuses a message with more than 50 blocks outright.
MAX_BLOCKS = 50

# Far enough back to find the previous due day for every frequency — biweekly
# is the widest at 14 days — without looping forever if a config matches none.
_MAX_LOOKBACK_DAYS = 15


@dataclass(frozen=True)
class DigestConfig:
    frequency: str
    hour: int
    weekday: int
    max_events: int
    repost_after_messages: int


def config_from_env() -> DigestConfig:
    return DigestConfig(
        frequency=env.digest_frequency,
        hour=env.digest_hour,
        weekday=env.digest_weekday,
        max_events=env.digest_max_events,
        repost_after_messages=env.digest_repost_after_messages,
    )


def is_posting_day(config: DigestConfig, day: date) -> bool:
    # "dailyish" comes up for consideration every day like "daily"; whether it
    # actually posts is decided later, in should_post.
    if config.frequency in ("daily", "dailyish"):
        return True

    if config.frequency == "weekly":
        return day.weekday() == config.weekday

    if config.frequency == "biweekly":
        if day.weekday() != config.weekday:
            return False
        # Matching days sit exactly seven apart, so the ordinal week index
        # flips parity each time and the digest lands every other week.
        return (day.toordinal() // 7) % 2 == 0

    return False


def last_due_at(config: DigestConfig, at: datetime) -> Optional[datetime]:
    """The most recent moment the digest was due, at or before `at`."""
    at = at.astimezone(timezone.utc)

    for days_back in range(_MAX_LOOKBACK_DAYS):
        day = (at - timedelta(days=days_back)).date()

        if not is_posting_day(config, day):
            continue

        due = datetime.combine(day, time(hour=config.hour), tzinfo=timezone.utc)

        if due <= at:
            return due

    return None


def _as_utc(value: datetime) -> datetime:
    """Event.StartTime is a naive Timestamp column.

    `datetime.timestamp()` reads a naive value as *server local* time, so the
    Slack date token would shift on any host that is not UTC. Pinning it here
    makes the rendered time independent of the container's timezone.
    """
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _event_blocks(event: dict[str, Any]) -> list[dict[str, Any]]:
    start = _as_utc(event["StartTime"])
    fallback = start.strftime("%A, %B %d at %I:%M %p")
    # Rendered in each reader's own timezone, which beats picking one for a
    # Slack full of people who are not in it.
    when = (
        f"<!date^{int(start.timestamp())}^{{date_long_pretty}} at {{time}}|{fallback}>"
    )

    raw = event.get("RawDescription")
    description = ""
    if raw:
        try:
            description = rich_text_to_mrkdwn(json.loads(raw)["elements"]).strip()
        except (ValueError, KeyError, TypeError):
            logger.warning("Unparseable RawDescription on event %s", event["id"])

    leader = f" - <@{event['LeaderSlackID']}>" if event.get("LeaderSlackID") else ""
    text = f"*{event['Title']}*{leader}\n"
    if description:
        text += f"{description}\n"
    text += f"*{when}*"

    section: dict[str, Any] = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": text},
    }

    if event.get("Avatar"):
        section["accessory"] = {
            "type": "image",
            "image_url": event["Avatar"],
            "alt_text": f"{event.get('Leader') or 'Event leader'} profile picture",
        }

    buttons: list[dict[str, Any]] = [
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "RSVP", "emoji": True},
            "style": "primary",
            "value": str(event["id"]),
            # Deliberately the same action_id the App Home button uses, so the
            # existing handler in isabelle/events/buttons/rsvp.py serves both.
            "action_id": "rsvp",
        }
    ]

    if event.get("CalendarLink"):
        buttons.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Add to GCal", "emoji": True},
                "url": event["CalendarLink"],
                "action_id": "add-to-gcal",
            }
        )

    return [{"type": "divider"}, section, {"type": "actions", "elements": buttons}]


def build_digest(
    events: list[dict[str, Any]], config: DigestConfig
) -> tuple[list[dict[str, Any]], str]:
    shown = events[: config.max_events]
    hidden = len(events) - len(shown)

    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📅 Upcoming Hack Club events",
                "emoji": True,
            },
        }
    ]

    for event in shown:
        blocks.extend(_event_blocks(event))

    footer = (
        f"And {hidden} more at <https://events.hackclub.com|events.hackclub.com>"
        if hidden > 0
        else "See them all at <https://events.hackclub.com|events.hackclub.com>"
    )
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": footer}]})

    text = (
        f"1 upcoming Hack Club event: {shown[0]['Title']}"
        if len(shown) == 1
        else f"{len(events)} upcoming Hack Club events"
    )

    return blocks, text


async def _get_row():
    return await DigestState.objects().get(DigestState.Key == STATE_KEY)


async def get_state() -> dict[str, Any]:
    row = await _get_row()

    if row is None:
        return {
            "last_posted_at": None,
            "last_checked_at": None,
            "last_message_ts": None,
            "last_event_ids": [],
        }

    return {
        "last_posted_at": row.LastPostedAt,
        "last_checked_at": row.LastCheckedAt,
        "last_message_ts": row.LastMessageTs or None,
        "last_event_ids": list(row.LastEventIds or []),
    }


async def _save_state(**fields) -> None:
    row = await _get_row()

    if row is None:
        row = DigestState({DigestState.Key: STATE_KEY})

    for name, value in fields.items():
        setattr(row, name, value)

    await row.save()


async def mark_checked(at: datetime) -> None:
    """Record that this slot was considered, whether or not it posted."""
    await _save_state(LastCheckedAt=at)


async def mark_posted(
    at: datetime, message_ts: Optional[str], event_ids: list[str]
) -> None:
    await _save_state(
        LastPostedAt=at,
        LastCheckedAt=at,
        LastMessageTs=message_ts or "",
        LastEventIds=event_ids,
    )


async def seed_state(at: Optional[datetime] = None) -> None:
    """Record the current moment as checked, without posting.

    Called once on startup so a fresh deploy waits for the next scheduled slot
    instead of firing a digest at whoever is in the channel right now.
    """
    if await _get_row() is not None:
        return

    at = at or datetime.now(timezone.utc)
    await _save_state(LastPostedAt=at, LastCheckedAt=at)


async def count_messages_since(message_ts: str, limit: int) -> int:
    """How many channel messages landed after the last digest.

    Capped at `limit`, because the only question asked of it is whether the
    digest has been pushed far enough up to be worth repeating. Thread replies
    do not appear in conversations.history, which is right: a reply inside a
    thread does not bury anything in the channel.
    """
    response = await client.conversations_history(
        channel=env.digest_channel,
        oldest=message_ts,
        inclusive=False,
        limit=limit,
    )
    return len(response.get("messages", []))


def shown_event_ids(events: list[dict[str, Any]], config: DigestConfig) -> list[str]:
    """The ids the digest would actually list.

    Compared against the previous run to decide whether a "dailyish" digest
    would be saying anything new. It is the *shown* slice rather than every
    upcoming event, because an event beyond the cap changes nothing a reader
    would see.
    """
    return [str(event["id"]) for event in events[: config.max_events]]


async def should_repost_unchanged(state: dict[str, Any], config: DigestConfig) -> bool:
    """Is the previous, identical digest buried deeply enough to repeat?"""
    last_ts = state["last_message_ts"]

    if not last_ts:
        # No idea where the last one landed, so no basis for calling it buried.
        return False

    try:
        messages = await count_messages_since(last_ts, config.repost_after_messages)
    except Exception:
        # A history read failing is not a reason to spam an unchanged digest.
        logger.exception("Could not count messages since the last digest")
        return False

    return messages >= config.repost_after_messages


async def maybe_post_digest(at: Optional[datetime] = None, force: bool = False) -> bool:
    if not env.digest_channel:
        return False

    at = at or datetime.now(timezone.utc)
    config = config_from_env()

    due = last_due_at(config, at)

    if due is None:
        return False

    state = await get_state()

    if not force:
        last_checked = state["last_checked_at"]

        if last_checked is not None and last_checked >= due:
            return False

    events = await env.database.get_upcoming_events()

    if not events:
        # Consume the slot anyway. Otherwise an empty calendar means retrying
        # every 60 seconds until an event happens to appear.
        await mark_checked(at)
        return False

    event_ids = shown_event_ids(events, config)

    if config.frequency == "dailyish" and not force:
        unchanged = state["last_event_ids"] and set(event_ids) == set(
            state["last_event_ids"]
        )

        if unchanged and not await should_repost_unchanged(state, config):
            # Same line-up, still visible. Burn the slot and look again
            # tomorrow rather than repeating yesterday's message.
            await mark_checked(at)
            return False

    blocks, text = build_digest(events, config)

    response = await client.chat_postMessage(
        channel=env.digest_channel,
        text=text,
        blocks=blocks,
        unfurl_links=False,
    )

    # Written only after Slack accepts the message. A crash before this point
    # retries on the next tick, which is the safer direction to fail.
    await mark_posted(at, response.get("ts"), event_ids)
    return True


async def digest_worker(interval_seconds: int = 60):
    while True:
        try:
            await maybe_post_digest()
        except Exception:
            logger.exception("Digest worker error")
        await asyncio.sleep(interval_seconds)


def init():
    if not env.digest_channel:
        logger.info("EVENTS_DIGEST_CHANNEL unset, not starting the digest worker")
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        raise RuntimeError(
            "digest.init() must be called from within a running asyncio loop."
        )

    async def _start():
        await seed_state()
        await digest_worker()

    loop.create_task(_start())
    logger.info(
        "Initialized %s event digest for channel %s",
        env.digest_frequency,
        env.digest_channel,
    )
