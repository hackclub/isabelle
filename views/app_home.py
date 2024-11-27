from datetime import datetime, timezone
from slack_sdk import WebClient

from utils.env import env
from utils.utils import user_in_safehouse, md_to_mrkdwn


def get_home(user_id: str, client: WebClient):
    sad_member = user_in_safehouse(user_id)
    user_info = client.users_info(user=user_id)
    ws_admin = (
        True
        if user_info["user"]["is_admin"]
        or user_info["user"]["is_owner"]
        or user_info["user"]["is_primary_owner"]
        else False
    )
    admin = True if user_id in env.authorised_users or ws_admin else False
    airtable_user = env.airtable.get_user(user_id)

    events = env.airtable.get_all_events(unapproved=True)
    upcoming_events = [
        event
        for event in events
        if datetime.fromisoformat(event["fields"]["Start Time"])
        > datetime.now(timezone.utc)
    ]
    current_events = [
        event
        for event in events
        if datetime.now(timezone.utc)
        < datetime.fromisoformat(event["fields"]["End Time"])
        and datetime.now(timezone.utc)
        > datetime.fromisoformat(event["fields"]["Start Time"])
    ]

    current_events_blocks = []
    for event in current_events:
        if not event["fields"].get("Approved", False) and (
            not event["fields"].get("Leader Slack ID", "") == user_id
            and not sad_member
            and not admin
        ):
            continue
        current_events_blocks.append({"type": "divider"})
        fallback_time = datetime.fromisoformat(event["fields"]["End Time"]).strftime(
            "Ends at %I:%M %p"
        )
        formatted_time = f"<!date^{int(datetime.fromisoformat(event['fields']['End Time']).timestamp())}^Ends at {{time}}|{fallback_time}>"
        mrkdwn = md_to_mrkdwn(event["fields"]["Description"])
        current_events_blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{'*[UNAPPROVED]:* ' if not event['fields'].get('Approved', False) else ''}*{event['fields']['Title']}* - <@{event['fields']['Leader Slack ID']}>\n{mrkdwn}\n*{formatted_time}*",
                },
                "accessory": {
                    "type": "image",
                    "image_url": event["fields"]["Avatar"][0]["url"],
                    "alt_text": f"{event['fields']['Leader']} profile picture",
                },
            }
        )
        buttons = []
        if admin and not event["fields"].get("Approved", False):
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve", "emoji": True},
                    "style": "primary",
                    "value": event["id"],
                    "action_id": "approve-event",
                }
            )
        buttons.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Join!", "emoji": True},
                "value": "join",
                "style": "primary",
                "url": event["fields"].get(
                    "Event Link", "https://hackclub.slack.com/archives/C07TNAZGMHS"
                ),  # Default to #high-seas-bulletin
            }
        )
        if user_id == event["fields"]["Leader Slack ID"] or admin:
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit", "emoji": True},
                    "value": event["id"],
                    "action_id": "edit-event",
                }
            )
        # if event["fields"].get("Approved", False):
        #     buttons.append(
        #         {
        #             "type": "button",
        #             "text": {"type": "plain_text", "text": "More Info", "emoji": True},
        #             "value": "more-info",
        #             "action_id": "more-info",
        #         }
        #     )
        current_events_blocks.append({"type": "actions", "elements": [*buttons]})

    upcoming_events_blocks = []
    for event in upcoming_events:
        if not event["fields"].get("Approved", False) and (
            not event["fields"].get("Leader Slack ID", "") == user_id
            and not sad_member
            and not admin
        ):
            continue
        upcoming_events_blocks.append({"type": "divider"})
        fallback_time = datetime.fromisoformat(event["fields"]["Start Time"]).strftime(
            "%A, %B %d at %I:%M %p"
        )
        formatted_time = f"<!date^{int(datetime.fromisoformat(event['fields']['Start Time']).timestamp())}^{{date_long_pretty}} at {{time}}|{fallback_time}>"
        mrkdwn = md_to_mrkdwn(event["fields"]["Description"])
        upcoming_events_blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{'*[UNAPPROVED]:* ' if not event['fields'].get('Approved', False) else ''}*{event['fields']['Title']}* - <@{event['fields']['Leader Slack ID']}>\n{mrkdwn}\n*{formatted_time}*",
                },
                "accessory": {
                    "type": "image",
                    "image_url": event["fields"]["Avatar"][0]["url"],
                    "alt_text": f"{event['fields']['Leader']} profile picture",
                },
            }
        )
        buttons = []
        if admin and not event["fields"].get("Approved", False):
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve", "emoji": True},
                    "style": "primary",
                    "value": event["id"],
                    "action_id": "approve-event",
                }
            )
        if user_id == event["fields"]["Leader Slack ID"] or admin:
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit", "emoji": True},
                    "value": event["id"],
                    "action_id": "edit-event",
                }
            )
        if not user_id == event["fields"]["Leader Slack ID"]:
            text = (
                ":bell: Interested"
                if airtable_user["id"]
                not in event["fields"].get("Interested Users", [])
                else ":white_check_mark: Going"
            )
            style_dict = (
                {"style": "primary"}
                if airtable_user["id"]
                not in event["fields"].get("Interested Users", [])
                else {}
            )

            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": text, "emoji": True},
                    "value": event["id"],
                    "action_id": "rsvp",
                    **style_dict,
                }
            )
        if event["fields"].get("Approved", False):
            # buttons.append(
            #     {
            #         "type": "button",
            #         "text": {"type": "plain_text", "text": "More Info", "emoji": True},
            #         "value": "more-info",
            #         "action_id": "more-info",
            #     }
            # )
            buttons.append(
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Add to GCal",
                        "emoji": True,
                    },
                    "url": event["fields"]["Calendar Link"],
                    "action_id": "add-to-gcal",
                }
            )
        upcoming_events_blocks.append({"type": "actions", "elements": [*buttons]})

    create_event_btn = [
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Add Event" if sad_member else "Propose Event",
                        "emoji": True,
                    },
                    "value": "host-event",
                    "action_id": "create-event" if sad_member else "propose-event",
                }
            ],
        }
    ]

    current_events_combined = (
        [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": (
                        "Current Events"
                        if len(current_events_blocks) > 1
                        else "Current Event"
                    ),
                    "emoji": True,
                },
            },
            *current_events_blocks,
        ]
        if len(current_events_blocks) > 0
        else []
    )

    upcoming_events_combined = (
        [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": (
                        "Upcoming Events"
                        if len(upcoming_events_blocks) > 1
                        else "Upcoming Event"
                    ),
                    "emoji": True,
                },
            },
            *upcoming_events_blocks,
        ]
        if len(upcoming_events_blocks) > 0
        else []
    )
    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":ac-isabelle-cheer: Hi {user_info['user']['profile']['display_name'] or user_info['user']['profile']['real_name']}!",
                    "emoji": True,
                },
            },
            *current_events_combined,
            {"type": "divider"},
            *create_event_btn,
            *upcoming_events_combined,
        ],
    }
