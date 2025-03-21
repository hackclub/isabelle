from typing import Any
from typing import Callable

from slack_sdk import WebClient

from isabelle.utils.env import env
from isabelle.views.app_home import get_home


def handle_rsvp_btn(ack: Callable, body: dict[str, Any], client: WebClient):
    ack()
    user_id = body["user"]["id"]
    event_id = body["actions"][0]["value"]
    user = env.airtable.rsvp_to_event(event_id, user_id)
    event = env.airtable.get_event(event_id)
    if event["id"] not in user["fields"].get("Interesting Events", []):
        client.chat_postMessage(
            channel=user_id,
            text=f"You're no longer interested in {event['fields']['Title']}! :(",
        )
    else:
        client.chat_postMessage(
            channel=user_id,
            text=f"You're interested in {event['fields']['Title']}! We'll let you know when it starts.",
        )

    client.views_publish(user_id=user_id, view=get_home(user_id, client))
