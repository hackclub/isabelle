from typing import Any
from typing import Callable
import logging

from slack_sdk.web.async_client import AsyncWebClient

from isabelle.utils.env import env
from isabelle.views.app_home import get_home


async def handle_approve_event_btn(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await ack()
    user_id = body["user"]["id"]

    if user_id not in env.authorised_users:
        await client.chat_postEphemeral(
            user=user_id,
            channel=user_id,
            text="You are not authorised to manage events.",
        )
        return

    value = body["actions"][0]["value"]

    event = await env.database.get_event(value)

    if not event:
        await client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text=f"Event with id `{value}` not found.",
        )
        return

    if event["Approved"]:
        await client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text=f"Event with id `{value}` has already been approved.",
        )
        return

    event = await env.database.update_event(value, **{"Approved": True})

    tags_str = ", ".join(t.replace("-", " ").title() for t in (event.get("Tags") or [])) if event.get("Tags") else "None"
    await client.chat_postMessage(
        user=body["user"]["id"],
        channel=env.slack_approval_channel,
        text=f"<@{user_id}> approved {event["Title"]} for <@{event["LeaderSlackID"]}>.\nTags: {tags_str}",
    )

    await client.chat_postMessage(
        channel=event["LeaderSlackID"],
        text=f"Your event {event["Title"]} has been approved by <@{user_id}>! Please reach out to them if you have any questions or need help.",
    )
    if env.mailer:
        try:
            user_info = await client.users_info(user=event["LeaderSlackID"])
            host_email = user_info["user"]["profile"].get("email")
            if host_email:
                #An example
                env.mailer.send_email(
                    host_email,
                    f"Your event `{event['Title']}' has been approved!",
                    f"Hi {event['Leader']}!\n\n"
                    f"Great news - your event `{event['Title']}` has been approved by <@{user_id}>.\n"
                    f"Start Time: {event['StartTime']}\n"
                    f"Event Link: {event.get('EventLink','N/A')}\n\n"
                    f"Reach out to <@{user_id}> if you have any question\n\n"

                )
        
        except Exception:
            logging.exception("Failed to send approval email")

    await client.views_publish(user_id=user_id, view=await get_home(user_id, client))
