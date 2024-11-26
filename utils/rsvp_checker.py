from slack_sdk import WebClient
from typing import Any
import schedule
import time
from datetime import datetime

from .env import env

client = WebClient(token=env.slack_bot_token)


def send_reminder(
    user_id: str, message: str, event: dict[str, Any], email: bool = False
):
    client.chat_postMessage(channel=user_id, text=message)
    if email:
        email_addr = client.users_info(user=user_id)["user"]["profile"]["email"]
        env.mailer.send_email(
            email_addr, f"{event["fields"]["Title"]} Reminder!", message
        )


def check_rsvps():
    events = env.airtable.get_all_events()

    for event in events:
        if not event["fields"].get("Approved", False):
            continue
        start_time = datetime.fromisoformat(event["fields"]["Start Time"]).timestamp()
        rsvps = env.airtable.get_rsvps_from_event(event["id"])

        # Handle 1 day reminders
        if start_time - time.time() <= 86400 and not event["fields"].get(
            "Sent 1 Day Reminder", False
        ):
            for user in rsvps:
                send_reminder(
                    user["fields"]["Slack ID"],
                    f"Hey! Just a reminder that {event['fields']['Title']} run by {event['fields']['Leader']} is tomorrow! Hope to see you there!",
                    event,
                )
            env.airtable.update_event(event["id"], **{"Sent 1 Day Reminder": True})

        # Handle 1 hour reminders
        elif start_time - time.time() <= 3600 and not event["fields"].get(
            "Sent 1 Hour Reminder", False
        ):
            for user in rsvps:
                send_reminder(
                    user["fields"]["Slack ID"],
                    f"Hey! Just a reminder that {event['fields']['Title']} run by {event['fields']['Leader']} starts in 1 hour! Hope to see you there!\nYou can join the event at {event['fields'].get('Event Link', 'the Slack!')}",
                    event,
                )
            env.airtable.update_event(event["id"], **{"Sent 1 Hour Reminder": True})

        elif start_time - time.time() <= 0 and not event["fields"].get(
            "Sent Started Reminder", False
        ):
            for user in rsvps:
                send_reminder(
                    user["fields"]["Slack ID"],
                    f"Hey! Just a reminder that {event['fields']['Title']} run by {event['fields']['Leader']} has started!\nYou can join the event at {event['fields'].get('Event Link', 'the Slack!')}\nHope you enjoy it!",
                    event,
                    email=True,
                )
            env.airtable.update_event(event["id"], **{"Sent Starting Reminder": True})


def rsvp_checker():
    schedule.every(1).minutes.do(check_rsvps)
    while True:
        schedule.run_pending()
        time.sleep(1)
