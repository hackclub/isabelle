from typing import Any, Callable
from slack_sdk import WebClient

from isabelle.utils.env import env
import json

def handle_reject_event_view(ack: Callable, body: dict[str, Any], client: WebClient):
    ack()
    view = body["view"]
    message = view["state"]["values"]["message"]["message"]["rich_text_value"]
    event_id = view["private_metadata"]

    event = env.airtable.get_event(event_id)

    if not event:
        client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text=f"Event with id `{event_id}` not found.",
        )
        return
    
    if event["fields"].get("Canceled", False):
        client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text=f"Event with id `{event_id}` has already been rejected.",
        )
        return
    
    event = env.airtable.update_event(event_id, **{"Canceled": True, "Raw Cancelation Reason": json.dumps(message)})

    client.chat_postMessage(
        channel=env.slack_approval_channel,
        text=f"<@{body['user']['id']}> rejected {event['fields']['Title']} for <@{event['fields']['Leader Slack ID']}> with the following reason.",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<@{body['user']['id']}> rejected {event['fields']['Title']} for <@{event['fields']['Leader Slack ID']}> with the following reason."
                }
            }, {
                "type": "divider",
            },
            message
        ]
    )

    client.chat_postMessage(
        channel=event["fields"]["Leader Slack ID"],
        text=f"Your event {event['fields']['Title']} has been rejected by <@{body['user']['id']}> with the following reason. Please reach out to them if you have any questions or need help.",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your event {event['fields']['Title']} has been rejected by <@{body['user']['id']}> :(\nPlease reach out to them if you have any questions or need help."
                }
            }, {
                "type": "divider",
            },
            message
        ]
    )

