import time
from datetime import datetime
from typing import Any
from threading import Thread
import asyncio


import schedule
from slack_sdk import WebClient

from .env import env

client = WebClient(token=env.slack_bot_token)


def send_reminder(
    user_id: str, message: str, event: dict[str, Any], email: bool = False
):
    client.chat_postMessage(channel=user_id, text=message)
    if email and env.mailer:
        pass
        email_addr = client.users_info(user=user_id)["user"]["profile"]["email"]
        env.mailer.send_email(
            email_addr, f"{event["Title"]} Reminder!", message
        )


async def check_rsvps():
    print("Checking rspvs async, its", time.time())
    events = await env.database.get_upcoming_events()

    for event in events:
        if not event["Approved"]:
            continue
        start_time = event["StartTime"].timestamp()
        rsvps = env.airtable.get_rsvps_from_event(str(event["id"]))

        # Handle 1 day reminders
        if start_time - time.time() <= 86400 and not event.get(
            "Sent1DayReminder", False
        ):
            for user in rsvps:
                send_reminder(
                    user,
                    f"Hey! Just a reminder that {event["Title"]} run by {event["Leader"]} is tomorrow! Hope to see you there!",
                    event,
                )
            env.airtable.update_event(str(event["id"]), **{"Sent1DayReminder": True})

        # Handle 1 hour reminders
        elif start_time - time.time() <= 3600 and not event.get(
            "Sent1HourReminder", False
        ):
            for user in rsvps:
                send_reminder(
                    user,
                    f"Hey! Just a reminder that {event["Title"]} run by {event["Leader"]} starts in 1 hour! Hope to see you there!\nYou can join the event at {event.get('EventLink', 'the Slack!')}",
                    event,
                )
            env.database.update_event(str(event["id"]), **{"Sent1HourReminder": True})

        elif start_time - time.time() <= 0 and not event.get(
            "SentStartingReminder", True
        ):
            pass
            for user in rsvps:
                send_reminder(
                    user,
                    f"Hey! Just a reminder that {event["Title"]} run by {event["Leader"]} has started!\nYou can join the event at {event.get('EventLink', 'the Slack!')}\nHope you enjoy it!",
                    event,
                    email=True,
                )
            env.database.update_event(str(event["id"]), **{"SentStartingReminder": True})

def _async_parser():
    #loop = asyncio.new_event_loop()
    #asyncio.set_event_loop(loop)
    #loop.run_until_complete(check_rsvps())
    #loop.close()
    asyncio.run(check_rsvps())

def check_rsvps_in_thread():
    thread = Thread(target=_async_parser)
    thread.start()

def init():
    schedule.every().minute.do(check_rsvps_in_thread)
    print("Initialized RSVP checker")
    rsvp_thread = Thread(target=rsvp_checker, daemon=True)
    rsvp_thread.start()


def rsvp_checker():
    while True:        
        schedule.run_pending()
        time.sleep(1)
