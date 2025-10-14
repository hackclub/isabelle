from typing import Any
from typing import Callable

from slack_sdk.web.async_client import AsyncWebClient

from isabelle.utils.env import env
from isabelle.views.app_home import get_home

async def handle_rsvp_btn(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await ack()
    user_id = body["user"]["id"]
    event_id = body["actions"][0]["value"]
    event = await env.database.toggle_user_interest(event_id, user_id)

    if not event:
        await client.chat_postMessage(
            channel=user_id,
            text=f"Error RSVPing! :(",
        )
        return

    if str(user_id) not in event.get("InterestedUsers", []):
        await client.chat_postMessage(
            channel=user_id,
            text=f"You're no longer interested in {event["Title"]}! :(",
        )
    else:
        await client.chat_postMessage(
            channel=user_id,
            text=f"You're interested in {event["Title"]}! We'll let you know when it starts.",
        )

    await client.views_publish(user_id=user_id, view=await get_home(user_id, client))
