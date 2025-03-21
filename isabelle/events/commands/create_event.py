from slack_sdk import WebClient

from isabelle.views.create_event import get_create_event_modal
from isabelle.utils.utils import user_in_safehouse

from typing import Any, Callable


def handle_create_event_cmd(ack: Callable, body: dict[str, Any], client: WebClient):
    ack()
    user_id = body["user_id"]
    sad_member = user_in_safehouse(user_id)

    if not sad_member:
        client.chat_postEphemeral(
            channel=body["channel_id"],
            user=body["user_id"],
            text="You are not authorised to create events. If you want to propose one, visit my app home page.",
        )
        return

    client.chat_postEphemeral(
        channel=body["channel_id"],
        user=body["user_id"],
        text="*Note: this command will be removed soon*. Please use my app home page to add an event.",
    )

    client.views_open(
        view=get_create_event_modal(user_id), trigger_id=body["trigger_id"]
    )
