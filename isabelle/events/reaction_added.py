
from slack_sdk.web.async_client import AsyncWebClient
from isabelle.utils.env import env
async def handle_reaction_added(body, client: AsyncWebClient):
    upcoming_events = await env.database.get_upcoming_events()

    if not upcoming_events:
        print("No upcoming events found")
        return
    
    # [(message_ts, channel_id, reaction_name, event_id)]
    events_rsvp_triggers = list(map(lambda e: tuple((e.get("rsvpMsg") or "none/none/none").split("/") + [str(e["id"])]),upcoming_events)) 

    event_to_rsvp = None

    for trigger in events_rsvp_triggers:
        (message_ts, channel_id, reaction_name, event_id) = trigger
        if (message_ts != body["event"]["item"]["ts"] or channel_id != body["event"]["item"]["channel"]):
            continue

        if reaction_name == "any" or reaction_name == body["event"]["reaction"]:
            event_to_rsvp = event_id
            break
    
    if event_to_rsvp is None:
        return
    
    event = await env.database.toggle_user_interest(event_to_rsvp,body["event"]["user"])

    if not event:
        await client.chat_postEphemeral(
        channel=body["event"]["item"]["channel"],
        user=body["event"]["user"],
        text='Error RSVPing to the event. :('
        )
        return
    if str(body["event"]["user"]) not in event.get("InterestedUsers", []):
        await client.chat_postEphemeral(
            channel=body["event"]["item"]["channel"],
            user=body["event"]["user"],
            text='Removed RSVP from the event. React again to toggle it back.'
        )
    else:
        await client.chat_postEphemeral(
            channel=body["event"]["item"]["channel"],
            user=body["event"]["user"],
            text='Successfully RSVPed to the event. You will receive reminders about the event.'
        )
    
