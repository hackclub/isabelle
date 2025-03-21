import json
from datetime import datetime

from isabelle.utils.env import env


def get_edit_event_modal(event_id: str):
    event = env.airtable.get_event(event_id)
    raw_desc = json.loads(event["fields"]["Raw Description"])
    return {
        "type": "modal",
        "callback_id": "edit_event",
        "private_metadata": event_id,
        "title": {"type": "plain_text", "text": "Add Event", "emoji": True},
        "submit": {"type": "plain_text", "text": "Submit", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "The event you create will need to be approved before being added to events.hackclub.com.\nPlease make sure that your event does not conflict with another event and that you fill out all of the information properly.",
                },
            },
            {"type": "divider"},
            {
                "type": "input",
                "block_id": "title",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "title",
                    "initial_value": event["fields"]["Title"],
                },
                "label": {"type": "plain_text", "text": "Title", "emoji": True},
            },
            {
                "type": "input",
                "block_id": "description",
                "element": {
                    "type": "rich_text_input",
                    "action_id": "description",
                    "initial_value": raw_desc,
                },
                "label": {"type": "plain_text", "text": "Description", "emoji": True},
            },
            {
                "type": "input",
                "block_id": "start_time",
                "element": {
                    "type": "datetimepicker",
                    "action_id": "start_time",
                    "initial_date_time": datetime.fromisoformat(
                        event["fields"]["Start Time"]
                    ).timestamp(),
                },
                "label": {"type": "plain_text", "text": "Start Time", "emoji": True},
            },
            {
                "type": "input",
                "block_id": "end_time",
                "element": {
                    "type": "datetimepicker",
                    "action_id": "end_time",
                    "initial_date_time": datetime.fromisoformat(
                        event["fields"]["End Time"]
                    ).timestamp(),
                },
                "label": {"type": "plain_text", "text": "End Time", "emoji": True},
            },
            {
                "type": "input",
                "block_id": "host",
                "element": {
                    "type": "users_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a host",
                        "emoji": True,
                    },
                    "initial_user": event["fields"]["Leader Slack ID"],
                    "action_id": "host",
                },
                "label": {"type": "plain_text", "text": "Host", "emoji": True},
            },
        ],
    }
