from slack_sdk import WebClient

from utils.env import env
from views.app_home import get_home

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

    value = body["actions"][0]["value"]

    event = env.airtable.get_event(value)

    if not event:
        client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text=f"Event with id `{value}` not found.",
        )
        return

    if event["fields"].get("Canceled", False):
        client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text=f"Event with id `{value}` has already been rejected.",
        )
        return

    event = env.airtable.update_event(value, **{"Canceled": True})

    client.chat_postMessage(
        user=body["user"]["id"],
        channel=env.slack_approval_channel,
        text=f"<@{user_id}> rejected {event['fields']['Title']} for <@{event['fields']['Leader Slack ID']}>.",
    )

    client.chat_postMessage(
        channel=event["fields"]["Leader Slack ID"],
        text=f"Your event {event['fields']['Title']} has been rejected by <@{user_id}>. They should have sent you a message about this, please reach out to them if they've not.",
    )

    client.views_publish(user_id=user_id, view=get_home(user_id, client))
