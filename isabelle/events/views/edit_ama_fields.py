import logging
from typing import Any
from typing import Callable

from slack_sdk.web.async_client import AsyncWebClient

from isabelle.utils.env import env
from isabelle.views.app_home import get_home


async def handle_edit_ama_fields_view(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await ack()
    user_id = body["user"]["id"]
    event_id = body["view"]["private_metadata"]
    values = body["view"]["state"]["values"]
    is_ama = values.get("ama").get("bool").get("selected_option").get("value") == "yes"
    avatar_url = values.get("amaavatar").get("ama-avatar").get("value")

    try:
        await env.database.update_event(event_id, **{"AMA": is_ama, "AMAAvatar": avatar_url})
        await client.chat_postEphemeral(
            user=user_id,
            channel=user_id,
            text="Successfully updated AMA fields."
        )
    except Exception:
        logging.warning("Error updating AMA fields", exc_info=True)
        await client.chat_postEphemeral(
            user=user_id,
            channel=user_id,
            text="Error updating AMA fields."
        )
