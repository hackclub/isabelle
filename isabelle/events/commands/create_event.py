from typing import Any
from typing import Callable

from slack_sdk.web.async_client import AsyncWebClient

from isabelle.utils.utils import user_in_safehouse
from isabelle.views.create_event import get_create_event_modal


async def handle_create_event_cmd(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await ack()
    user_id = body["user_id"]
    sad_member = await user_in_safehouse(user_id)

    if not sad_member:
        await client.chat_postEphemeral(
            channel=body["channel_id"],
            user=body["user_id"],
            text="You are not authorised to create events. If you want to propose one, visit my app home page.",
        )
        return

    await client.chat_postEphemeral(
        channel=body["channel_id"],
        user=body["user_id"],
        text="*Note: this command will be removed soon*. Please use my app home page to add an event.",
    )

    await client.views_open(
        view=get_create_event_modal(user_id), trigger_id=body["trigger_id"]
    )
