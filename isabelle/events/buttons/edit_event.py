from typing import Any
from typing import Callable

from slack_sdk.web.async_client import AsyncWebClient

from isabelle.views.edit_event import get_edit_event_modal


async def handle_edit_event_btn(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await ack()
    value = body["actions"][0]["value"]
    await client.views_open(view= await get_edit_event_modal(value), trigger_id=body["trigger_id"])
