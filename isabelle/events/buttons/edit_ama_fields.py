from slack_sdk.web.async_client import AsyncWebClient

from isabelle.views.edit_ama_fields import get_edit_ama_fields_modal

async def handle_edit_ama_fields_btn(ack, body, client: AsyncWebClient):
    await ack()
    value = body["actions"][0]["value"]
    view = await get_edit_ama_fields_modal(value)
    await client.views_open(view=view, trigger_id=body["trigger_id"])
