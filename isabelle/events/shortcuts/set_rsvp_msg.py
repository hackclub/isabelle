from isabelle.utils.utils import user_in_safehouse
from isabelle.utils.env import env
from slack_sdk.web.async_client import AsyncWebClient
from blockkit import Modal, Input, RichTextInput, StaticSelect, Option, Markdown, RichText, RichTextSection, RichTextEl


async def handle_set_rsvp_msg(ack, shortcut,body, client: AsyncWebClient):
    await ack()
    user_id = shortcut["user"]["id"]
    sad_member = await user_in_safehouse(user_id)

    
    if not sad_member:
        await client.chat_postEphemeral(
            channel=shortcut["channel"]["id"],
            user=shortcut["user"]["id"],
            text="You are not authorized to set announcement messages. Ask a SAD member to do so.",
        )
        return
    
    upcoming_events = env.airtable.get_upcoming_events()
    upcoming_events = list(map(lambda x: (x["fields"]["Title"], x["id"]), upcoming_events))
    upcoming_events = list(map(lambda x: Option(x[0],x[1]), upcoming_events))
    if len(upcoming_events) == 0:
        upcoming_events = [Option("No upcoming events", "none")]

    modal = (
    Modal()
    .title("Confirm")
    .add_block(
        RichText().add_element(
            RichTextSection()
                .add_element(RichTextEl("Set this message as an event announcement message."))
        )
    )
    .add_block(
        Input("Emoji")
            .block_id("emoji")
            .optional(True)
            .element(
                RichTextInput().action_id("selected_emoji")
            )
            .hint("Put only one emoji. Optional, if left unset all reactions will be considered RSVP")
    )
    .add_block(
        Input("Event")
        .block_id("chosen_event")
            .optional(False)
            .element(
                StaticSelect(options=upcoming_events).action_id("event_select")
            )
    )
    .private_metadata(f"{shortcut["message"]["ts"]}-{shortcut["channel"]["id"]}")
    .submit("Confirm")
    .callback_id("rsvp_msg_set_response")
    .build()
)

    await client.views_open(
        trigger_id=shortcut["trigger_id"],
        view=modal
    )