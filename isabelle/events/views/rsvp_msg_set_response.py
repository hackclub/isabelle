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

    ev = await env.database.set_rsvp_msg(chosen_event_id, message_ts, channel_id, emoji_name)

    if ev and ev.get("rsvpMsg","") != "":
        await client.chat_postEphemeral(
            channel=channel_id,
            user=body["user"]["id"],
            text="Successfully set RSVP message for the event."
        )
    else:
        await client.chat_postEphemeral(
            channel=channel_id,
            user=body["user"]["id"],
            text="Error setting RSVP message for the event."
        )

    await rsvp_previous_reactions(client=client, message_ts=message_ts, channel_id=channel_id, reaction_name=emoji_name, event_id=chosen_event_id)
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

async def rsvp_previous_reactions(client: AsyncWebClient, message_ts: str, channel_id: str, reaction_name: str | None, event_id: str):
    res = await client.reactions_get(timestamp=message_ts, channel=channel_id, full=True)

    msg_url = (await client.chat_getPermalink(channel=channel_id, message_ts=message_ts)).get("permalink")

    if not res.get("ok"):
        return
    
    reactions: list = res.get("message").get("reactions")

    # Holy ternary shenanigans. I'm so sorry for this, seems like the python way
    reactions = [i for i in reactions if i.get("name") == reaction_name] if reaction_name else reactions

    users = [user for reaction in reactions for user in reaction["users"]]

    users = set(users)

    for user_id in users:
        event_to_rsvp = event_id
        event = await env.database.toggle_user_interest(event_to_rsvp,user_id)

        if not event:
            print(f'Error trying to retroactively RSVP {user_id}')
        else:
            try: 
                await client.chat_postMessage(
                    channel=user_id,
                    text=f'You previously had shown interest on <{msg_url}|an event>. You will receive reminders about the event. To remove your interest, remove your reaction in the announcement message.'
                    )
            except Exception:
                pass


    pass