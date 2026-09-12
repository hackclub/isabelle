from datetime import datetime
from datetime import timezone

ONE_DAY = 86400
ONE_HOUR = 3600

STARTING = "starting"
HOUR = "hour"
DAY = "day"

SENT_FLAGS = {
    DAY: ("Sent1DayReminder",),
    HOUR: ("Sent1DayReminder", "Sent1HourReminder"),
    STARTING: ("Sent1DayReminder", "Sent1HourReminder", "SentStartingReminder"),
}


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seconds_until_start(event, now=None):
    start = event.get("StartTime")
    if not start:
        return None
    return (start - (now or utc_now())).total_seconds()


def due_reminder(event, now=None):
    if not event.get("Approved") or event.get("Cancelled"):
        return None

    remaining = seconds_until_start(event, now)
    if remaining is None:
        return None

    if remaining <= 0:
        return None if event.get("SentStartingReminder") else STARTING
    if remaining <= ONE_HOUR:
        return None if event.get("Sent1HourReminder") else HOUR
    if remaining <= ONE_DAY:
        return None if event.get("Sent1DayReminder") else DAY
    return None


def message_for(kind, event):
    title = event.get("Title")
    leader = event.get("Leader")
    where = event.get("EventLink") or "the Slack"

    if kind == STARTING:
        return (
            f"{title} run by {leader} is starting now!\n"
            f"You can join at {where}\nHope you enjoy it!"
        )
    if kind == HOUR:
        return (
            f"Hey! Just a reminder that {title} run by {leader} starts in 1 hour! "
            f"Hope to see you there!\nYou can join the event at {where}"
        )
    return (
        f"Hey! Just a reminder that {title} run by {leader} is tomorrow! "
        "Hope to see you there!"
    )


def flags_to_set(kind):
    return {flag: True for flag in SENT_FLAGS[kind]}
