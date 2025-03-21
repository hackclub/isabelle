from typing import Any
from typing import Callable

from slack_sdk import WebClient

from isabelle.utils.env import env
from isabelle.views.app_home import get_home


def handle_approve_event_btn(ack: Callable, body: dict[str, Any], client: WebClient):
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

    if event["fields"].get("Approved", False):
        client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text=f"Event with id `{value}` has already been approved.",
        )
        return

    event = env.airtable.update_event(value, **{"Approved": True})

    client.chat_postMessage(
        user=body["user"]["id"],
        channel=env.slack_approval_channel,
        text=f"<@{user_id}> approved {event['fields']['Title']} for <@{event['fields']['Leader Slack ID']}>.",
    )

    client.chat_postMessage(
        channel=event["fields"]["Leader Slack ID"],
        text=f"Your event {event['fields']['Title']} has been approved by <@{user_id}>! Please reach out to them if you have any questions or need help.",
    )

    client.views_publish(user_id=user_id, view=get_home(user_id, client))
