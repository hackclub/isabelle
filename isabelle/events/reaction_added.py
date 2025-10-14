# TODO: REWRITE LOGIC

from slack_sdk.web.async_client import AsyncWebClient
from isabelle.utils.env import env
async def handle_reaction_added(body, client: AsyncWebClient):
    upcoming_events = env.airtable.get_upcoming_events()

    if not upcoming_events:
        print("No upcoming events found")
        return
    
    # [(message_ts, channel_id, reaction_name, event_id)]
    events_rsvp_triggers = list(map(lambda e: tuple((e["fields"].get("rsvp-msg") or "none-none-none").split("-") + [e["id"]]),upcoming_events)) 

    event_to_rsvp = None

    for trigger in events_rsvp_triggers:
        (message_ts, channel_id, reaction_name, event_id) = trigger
        if (message_ts != body["event"]["item"]["ts"] or channel_id != body["event"]["item"]["channel"]):
            pass

        if reaction_name == "any" or reaction_name == body["event"]["reaction"]:
            event_to_rsvp = event_id
            break
    
    if event_to_rsvp is None:
        return
    
    env.airtable.rsvp_to_event(event_to_rsvp,body["event"]["user"])

    await client.chat_postEphemeral(
        channel=body["event"]["item"]["channel"],
        user=body["event"]["user"],
        text='Successfully RSVPed to the event. You will receive reminders about the event.'
    )
    
    pass
