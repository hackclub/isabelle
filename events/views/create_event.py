from typing import Any, Callable
from slack_sdk import WebClient
from datetime import datetime, timezone

from utils.env import env
from utils.utils import rich_text_to_md, rich_text_to_mrkdwn
from views.app_home import get_home
import json


def handle_create_event_view(ack: Callable, body: dict[str, Any], client: WebClient):
    ack()
    view = body["view"]
    values = view["state"]["values"]
    title = (values["title"]["title"]["value"],)
    description = values["description"]["description"]["rich_text_value"]["elements"]
    md = rich_text_to_md(description)
    start_time = (values["start_time"]["start_time"]["selected_date_time"],)
    end_time = (values["end_time"]["end_time"]["selected_date_time"],)
    host_id = values["host"]["host"]["selected_user"]
    location = (
        values.get("location", {}).get("location", {}).get("value")
        or "https://hackclub.slack.com/archives/C07TNAZGMHS"
    )

    user = client.users_info(user=host_id)
    host_name = user["user"]["real_name"]
    host_pfp = user["user"]["profile"]["image_192"]

    event = env.airtable.create_event(
        title[0],
        md,
        description,
        start_time[0],
        end_time[0],
        location,
        host_id,
        host_name,
        host_pfp,
    )
    if not event:
        client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text=f'An error occurred whilst creating the event "{title[0]}".',
        )

    fallback_start_time = datetime.fromtimestamp(
        start_time[0], timezone.utc
    ).isoformat()
    fallback_end_time = datetime.fromtimestamp(end_time[0], timezone.utc).isoformat()

    user_id = body.get("user", {}).get("id", "")
    host_mention = f"for <@{host_id}>" if host_id != user_id else ""
    host_str = f"<@{user_id}> {host_mention}"
    rich_text = json.loads(event["fields"]["Raw Description"])
    mrkdwn = rich_text_to_mrkdwn(rich_text)
    client.chat_postMessage(
        channel=env.slack_approval_channel,
        text=f"New event request by <@{body['user']['id']}>!\nTitle: {title[0]}\nDescription: {mrkdwn}\nStart Time: {start_time[0]}\nEnd Time: {end_time[0]}",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"New event request by {host_str}!\n*Title:* {title[0]}\n*Description:* {mrkdwn}\n*Start Time (local time):* <!date^{start_time[0]}^{{date_num}} at {{time_secs}}|{fallback_start_time}>\n*End Time (local time):* <!date^{end_time[0]}^{{date_num}} at {{time_secs}}|{fallback_end_time}>",
                },
            }
        ],
    )

    client.views_publish(user_id=user_id, view=get_home(user_id, client))
