from slack_sdk.web.async_client import AsyncWebClient
from isabelle.utils.env import env

async def handle_rsvp_msg_set_response(ack: callable, body, view, client: AsyncWebClient):
    await ack()

    emoji_name = extract_emoji_name(view)
    chosen_event_id = view["state"]["values"]["chosen_event"]["event_select"]["selected_option"]["value"]
    (message_ts, channel_id) = tuple(view["private_metadata"].split("-"))
    try:
        await client.reactions_add(
            channel=channel_id,
            timestamp=message_ts,
            name=emoji_name
        )
    except Exception as e:
        print("Error reacting@handle_rsvp_msg_set_response ",e)
        pass

    env.airtable.set_rsvp_msg(chosen_event_id, message_ts, channel_id, emoji_name)

    pass


def extract_emoji_name(view):
    emoji_name = None
    try:
        rich_text_value = view["state"]["values"]["emoji"]["selected_emoji"]["rich_text_value"]
        elements = rich_text_value["elements"][0]["elements"]
        
        for element in elements:
            if element["type"] == "emoji":
                emoji_name = element["name"]
                break
    except (KeyError, IndexError):
        # No emoji was selected or there was an issue parsing
        emoji_name = None

    return emoji_name