import asyncio
import logging
from typing import Any

from slack_sdk.web.async_client import AsyncWebClient

from isabelle.reminders import due_reminder
from isabelle.reminders import flags_to_set
from isabelle.reminders import message_for
from isabelle.reminders import utc_now

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
    now = utc_now()
    events = await env.database.get_reminder_candidates()

    for event in events:
        kind = due_reminder(event, now)
        if not kind:
            continue

        message = message_for(kind, event)

        for user_id in _slack_ids_for_event(event):
            try:
                await send_reminder(user_id, message, event)
            except Exception:
                logger.exception(
                    "Could not remind %s about %s", user_id, event.get("Title")
                )

        await env.database.update_event(str(event["id"]), **flags_to_set(kind))


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
