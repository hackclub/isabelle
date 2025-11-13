import json
from typing import Any
from typing import Callable

from slack_sdk.web.async_client import AsyncWebClient

from isabelle.utils.env import env


async def handle_reject_event_view(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await ack()
    view = body["view"]
    message = view["state"]["values"]["message"]["message"]["rich_text_value"]
    event_id = view["private_metadata"]

    event = await env.database.get_event(event_id)
    print(f'rejecting event: {event}')

    if not event:
        await client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text=f"Event with id `{event_id}` not found.",
        )
        return

    if event.get("Cancelled", False):
        await client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text=f"Event with id `{event_id}` has already been rejected.",
        )
        return

    event = await env.database.update_event(
        event_id, **{"Cancelled": True, "RawCancellation": json.dumps(message)}
    )

    await client.chat_postMessage(
        channel=env.slack_approval_channel,
        text=f"<@{body['user']['id']}> rejected {event["Title"]} for <@{event["LeaderSlackID"]}> with the following reason.",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<@{body['user']['id']}> rejected {event["Title"]} for <@{event["LeaderSlackID"]}> with the following reason.",
                },
            },
            {
                "type": "divider",
            },
            message,
        ],
    )

    await client.chat_postMessage(
        channel=event["LeaderSlackID"],
        text=f"Your event {event["Title"]} has been rejected by <@{body['user']['id']}> with the following reason. Please reach out to them if you have any questions or need help.",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your event {event["Title"]} has been rejected by <@{body['user']['id']}> :(\nPlease reach out to them if you have any questions or need help.",
                },
            },
            {
                "type": "divider",
            },
            message,
        ],
    )
