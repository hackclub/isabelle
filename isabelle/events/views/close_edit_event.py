from isabelle.utils.env import env
from isabelle.views.reject_event import get_reject_event_modal
from blockkit import Message, Section, Actions, Button
from slack_sdk.web.async_client import AsyncWebClient

async def handle_close_edit_event(ack, body, client: AsyncWebClient):
    await ack()
    user_id = body["user"]["id"]

    if user_id not in env.authorised_users:
        return

    event_id = body["view"]["private_metadata"] 

    message = (
        Message()
            .add_block(Section("Do you want to do anything else with this event?"))
            .add_block(
                Actions()
                    .add_element(Button("Cancel event").style('danger').value(event_id).action_id("reject-event"))
            )
        ).build()

    await client.chat_postEphemeral(
        user=user_id,
        channel=user_id,
        blocks=message["blocks"]
    )
