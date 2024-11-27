from slack_sdk import WebClient

from views.edit_event import get_edit_event_modal

from typing import Any, Callable


def handle_edit_event_btn(ack: Callable, body: dict[str, Any], client: WebClient):
    ack()
    value = body["actions"][0]["value"]
    client.views_open(
    view=get_edit_event_modal(value), trigger_id=body["trigger_id"]
    )
