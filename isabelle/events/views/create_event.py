import json
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Callable
from urllib.parse import urlparse

from slack_sdk.web.async_client import AsyncWebClient

from isabelle.utils.env import env
from isabelle.utils.utils import rich_text_to_md
from isabelle.utils.utils import rich_text_to_mrkdwn
from slack_gfm import rich_text_to_gfm

from isabelle.views.app_home import get_home
from datetime import datetime


async def handle_create_event_view(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await ack()
    view = body["view"]
    values = view["state"]["values"]
    title = (values["title"]["title"]["value"],)
    description = values["description"]["description"]["rich_text_value"]["elements"]
    md = rich_text_to_md(description)
    start_time = datetime.fromtimestamp(values["start_time"]["start_time"]["selected_date_time"])
    end_time = datetime.fromtimestamp(values["end_time"]["end_time"]["selected_date_time"])
    host_id = values["host"]["host"]["selected_user"]
    location = (
        values.get("location", {}).get("location", {}).get("value")
        or "https://app.slack.com/huddle/T0266FRGM/C01D7AHKMPF"
    )
    rsvp_form_url = values.get("rsvp_form_url", {}).get("rsvp_form_url", {}).get("value") or None

    user = await client.users_info(user=host_id)
    host_name = user["user"]["real_name"]

    tags_block = values.get("tags", {}).get("tags", {})
    tags = [opt["value"] for opt in tags_block.get("selected_options", [])]

    if not urlparse(location).scheme or not urlparse(location).netloc:
        await client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text='The event location must be an URL.'
        )
        return

    if rsvp_form_url and (not urlparse(rsvp_form_url).scheme or not urlparse(rsvp_form_url).netloc):
        await client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text='The external RSVP link must be a URL.'
        )
        return

    event = await env.database.create_event(
        title=title[0],
        description=md,
        raw_description=description,
        start_time=start_time,
        end_time=end_time,
        leader_slack_id=host_id,
        leader_name=host_name,
        event_link=location,
        tags=tags if tags else None,
        rsvp_form_url=rsvp_form_url,
    )
    if not event:
        await client.chat_postEphemeral(
            user=body["user"]["id"],
            channel=body["user"]["id"],
            text=f'An error occurred whilst creating the event "{title[0]}".',
        )
        return

    fallback_start_time = start_time.isoformat()
    fallback_end_time = end_time.isoformat()

    user_id = body.get("user", {}).get("id", "")
    host_mention = f"for <@{host_id}>" if host_id != user_id else ""
    host_str = f"<@{user_id}> {host_mention}"
    rich_text = json.loads(event["RawDescription"])
    mrkdwn = rich_text_to_gfm(rich_text)
    tags_str = ", ".join(t.replace("-", " ").title() for t in tags) if tags else "None"
    rsvp_form_url_str = rsvp_form_url or "None"
    await client.chat_postMessage(
        channel=env.slack_approval_channel,
        text=f"New event request by <@{body['user']['id']}>!\nTitle: {title[0]}\nDescription: {mrkdwn}\nTags: {tags_str}\nStart Time: {start_time}\nEnd Time: {end_time}\nExternal RSVP Link: {rsvp_form_url_str}",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"New event request by {host_str}!\n*Title:* {title[0]}\n*Description:* {mrkdwn}\n*Tags:* {tags_str}\n*Start Time (local time):* <!date^{int(start_time.timestamp())}^{{date_num}} at {{time_secs}}|{fallback_start_time}>\n*End Time (local time):* <!date^{int(end_time.timestamp())}^{{date_num}} at {{time_secs}}|{fallback_end_time}>\n*External RSVP Link:* {rsvp_form_url_str}",
                },
            }
        ],
    )

    await client.views_publish(user_id=user_id, view=await get_home(user_id, client))
