import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from slack_sdk.web.async_client import AsyncWebClient

from .env import env

client = AsyncWebClient(token=env.slack_bot_token)
logger = logging.getLogger(__name__)


async def send_reminder(
    user_id: str, message: str, event: dict[str, Any], email: bool = False
):
    await client.chat_postMessage(channel=user_id, text=message)
    if email and env.mailer:
        pass
        info = await client.users_info(user=user_id)
        email_addr = info["user"]["profile"]["email"]
        env.mailer.send_email(
            email_addr, f"{event['Title']} Reminder!", message
        )

def _slack_ids_for_event(event: dict[str, Any]) -> list[str]:
    rsvp_data: dict = event.get("RSVPData") or {} 
    legacy: list = event.get("InterestedUsers") or []
    ids: list[str] = []
    seen: set[str] = set()
    for entry in rsvp_data.values():
        sid = entry.get("slackId")
        if sid and sid not in seen:
            ids.append(sid); seen.add(sid)
    for sid in legacy:
        if sid and sid not in seen:
            ids.append(sid); seen.add(sid)
    return ids

async def check_rsvps():
    logger.debug("Checking RSVPs")
    events = await env.database.get_upcoming_events()

    for event in events:
        if not event["Approved"]:
            continue
        start_time = event["StartTime"].timestamp()
        slack_ids = _slack_ids_for_event(event)

        # Handle 1 day reminders
        if start_time - time.time() <= 86400 and not event.get(
            "Sent1DayReminder", False
        ):
            for user_id in slack_ids:
                await send_reminder(
                    user_id,
                    f"Hey! Just a reminder that {event['Title']} run by {event['Leader']} is tomorrow! Hope to see you there!",
                    event,
                )
            await env.database.update_event(str(event["id"]), **{"Sent1DayReminder": True})

        # Handle 1 hour reminders
        elif start_time - time.time() <= 3600 and not event.get(
            "Sent1HourReminder", False
        ):
            for user_id in slack_ids:
                await send_reminder(
                    user_id,
                    f"Hey! Just a reminder that {event['Title']} run by {event['Leader']} starts in 1 hour! Hope to see you there!\nYou can join the event at {event.get('EventLink', 'the Slack!')}",
                    event,
                )
            await env.database.update_event(str(event["id"]), **{"Sent1HourReminder": True})

        elif start_time - time.time() <= 0 and not event.get(
            "SentStartingReminder", True
        ):
            pass
            for user_id in slack_ids:
                await send_reminder(
                    user_id,
                    f"Hey! Just a reminder that {event['Title']} run by {event['Leader']} has started!\nYou can join the event at {event.get('EventLink', 'the Slack!')}\nHope you enjoy it!",
                    event,
                    email=True,
                )
            await env.database.update_event(str(event["id"]), **{"SentStartingReminder": True})


async def rsvp_worker(interval_seconds = 60):
    while True:
        try:
            await check_rsvps()
        except Exception:
            logger.exception("RSVP worker error")
        await asyncio.sleep(interval_seconds)


def init():
    try:
        loop = asyncio.get_running_loop() 
    except RuntimeError:
        raise RuntimeError(
            "rsvp_checker.init() must be called from within a running asyncio loop."
        )
    loop.create_task(check_rsvps())   # check at startup
    loop.create_task(rsvp_worker())   # periodic worker
    logger.info("Initialized RSVP checker")
