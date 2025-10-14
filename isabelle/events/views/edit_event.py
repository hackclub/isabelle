import json
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Callable

from slack_sdk.web.async_client import AsyncWebClient

from isabelle.utils.env import env
from isabelle.utils.utils import rich_text_to_md
from isabelle.utils.utils import rich_text_to_mrkdwn
from isabelle.views.app_home import get_home


async def handle_edit_event_view(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await ack()
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
        or "https://app.slack.com/huddle/T0266FRGM/C01D7AHKMPF"
    )

    user = await client.users_info(user=host_id)
    host_name = user["user"]["real_name"]
    # TODO: Use cachet
    host_pfp = user["user"]["profile"]["image_192"]

    raw_description_string = json.dumps(
        {
            "type": "rich_text",
            "elements": description,
        }
    )

    event = await env.database.update_event(
        event_id=body["view"]["private_metadata"],
        **{
            "Title": title[0],
            "Description": md,
            "RawDescription": raw_description_string,
            "StartTime": datetime.fromtimestamp(
                start_time[0]
            ),
            "EndTime": datetime.fromtimestamp(end_time[0]),
            "EventLink": location,
            "LeaderSlackID": host_id,
            "Leader": host_name,
            "Avatar": host_pfp,
        },
    )
    if not event:
        await client.chat_postEphemeral(
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
    rich_text = json.loads(raw_description_string)
    mrkdwn = rich_text_to_mrkdwn(rich_text)
    await client.chat_postMessage(
        channel=env.slack_approval_channel,
        text=f"Event updated by <@{body['user']['id']}>!\nTitle: {title[0]}\nDescription: {mrkdwn}\nStart Time: {start_time[0]}\nEnd Time: {end_time[0]}",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Event updated by {host_str}!\n*Title:* {title[0]}\n*Description:* {mrkdwn}\n*Start Time (local time):* <!date^{start_time[0]}^{{date_num}} at {{time_secs}}|{fallback_start_time}>\n*End Time (local time):* <!date^{end_time[0]}^{{date_num}} at {{time_secs}}|{fallback_end_time}>",
                },
            }
        ],
    )

    await client.views_publish(user_id=user_id, view=await get_home(user_id, client))
