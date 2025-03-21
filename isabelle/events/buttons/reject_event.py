from slack_sdk import WebClient

from isabelle.utils.env import env
from isabelle.views.reject_event import get_reject_event_modal

from typing import Any, Callable


def handle_reject_event_btn(ack: Callable, body: dict[str, Any], client: WebClient):
    ack()
    user_id = body["user"]["id"]

    if user_id not in env.authorised_users:
        client.chat_postEphemeral(
            user=user_id,
            channel=user_id,
            text="You are not authorised to manage events.",
        )
        return

    event_id = body["actions"][0]["value"]

    client.views_open(user_id=user_id, view=get_reject_event_modal(event_id), trigger_id=body["trigger_id"])
