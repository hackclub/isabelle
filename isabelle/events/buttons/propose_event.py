from typing import Any
from typing import Callable

from slack_sdk import WebClient

from isabelle.views.propose_event import get_propose_event_modal


def handle_propose_event_btn(ack: Callable, body: dict[str, Any], client: WebClient):
    ack()
    user_id = body["user"]["id"]
    client.views_open(
        view=get_propose_event_modal(user_id), trigger_id=body["trigger_id"]
    )
