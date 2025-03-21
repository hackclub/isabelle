from slack_sdk import WebClient

from isabelle.views.create_event import get_create_event_modal

from typing import Any, Callable


def handle_create_event_btn(ack: Callable, body: dict[str, Any], client: WebClient):
    ack()
    user_id = body["user"]["id"]
    client.views_open(
        view=get_create_event_modal(user_id), trigger_id=body["trigger_id"]
    )
