import json
from datetime import datetime
from datetime import timezone

from slack_sdk.web.async_client import AsyncWebClient

from isabelle.utils.env import env
from isabelle.utils.utils import rich_text_to_mrkdwn
from isabelle.utils.utils import user_in_safehouse


async def get_home(user_id: str, client: AsyncWebClient):
    sad_member = await user_in_safehouse(user_id)
    user_info = await client.users_info(user=user_id)
    ws_admin = (
        True
        if user_info["user"]["is_admin"]
        or user_info["user"]["is_owner"]
        or user_info["user"]["is_primary_owner"]
        else False
    )
    admin = True if user_id in env.authorised_users or ws_admin else False
    # airtable_user = env.airtable.get_user(user_id)

    events = await env.database.get_all_events(include_unapproved=True)

    upcoming_events = [
        event
        for event in events
        if event["StartTime"]
        > datetime.now()
    ]
    current_events = [
        event
        for event in events
        if datetime.now()
        < event.get("EndTime")
        and datetime.now()
        > event["StartTime"]
    ]

    current_events_blocks = []
    for event in current_events:
        if not event["Approved"] and (
            not event["LeaderSlackID"] == user_id
            and not sad_member
            and not admin
        ):
            continue
        current_events_blocks.append({"type": "divider"})
        fallback_time = event["EndTime"].strftime(
            "Ends at %I:%M %p"
        )
        formatted_time = f"<!date^{int(event["EndTime"].timestamp())}^Ends at {{time}}|{fallback_time}>"
        rich_text = json.loads(event["RawDescription"])
        mrkdwn = rich_text_to_mrkdwn(rich_text["elements"])
        current_events_blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{'*[UNAPPROVED]:* ' if not event["Approved"] else ''}*{event["Title"]}* - <@{event["LeaderSlackID"]}>\n{mrkdwn}\n*{formatted_time}*",
                },
                "accessory": {
                    "type": "image",
                    "image_url": event["Avatar"],
                    "alt_text": f"{event["Leader"]} profile picture",
                },
            }
        )
        buttons = []
        if admin and not event["Approved"]:
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve", "emoji": True},
                    "style": "primary",
                    "value": str(event["id"]),
                    "action_id": "approve-event",
                }
            )
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject", "emoji": True},
                    "style": "danger",
                    "value": str(event["id"]),
                    "action_id": "reject-event",
                }
            )
        buttons.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Join!", "emoji": True},
                "value": "join",
                "style": "primary",
                "url": event["EventLink"],  # Defaults to #community huddle
            }
        )
        if user_id == event["LeaderSlackID"] or admin:
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit", "emoji": True},
                    "value": str(event["id"]),
                    "action_id": "edit-event",
                }
            )
        # if event["Approved"]:
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
        if not event["Approved"] and (
            not event["LeaderSlackID"] == user_id
            and not sad_member
            and not admin
        ):
            continue
        upcoming_events_blocks.append({"type": "divider"})
        fallback_time = event["StartTime"].strftime(
            "%A, %B %d at %I:%M %p"
        )
        formatted_time = f"<!date^{int(event["StartTime"].timestamp())}^{{date_long_pretty}} at {{time}}|{fallback_time}>"
        rich_text = json.loads(event["RawDescription"])
        mrkdwn = rich_text_to_mrkdwn(rich_text["elements"])
        upcoming_events_blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{'*[UNAPPROVED]:* ' if not event["Approved"] else ''}*{event["Title"]}* - <@{event["LeaderSlackID"]}>\n{mrkdwn}\n*{formatted_time}*",
                },
                "accessory": {
                    "type": "image",
                    "image_url": event["Avatar"],
                    "alt_text": f"{event["Leader"]} profile picture",
                },
            }
        )
        buttons = []
        if admin and not event["Approved"]:
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve", "emoji": True},
                    "style": "primary",
                    "value": str(event["id"]),
                    "action_id": "approve-event",
                }
            )
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject", "emoji": True},
                    "style": "danger",
                    "value": str(event["id"]),
                    "action_id": "reject-event",
                }
            )
        if user_id == event["LeaderSlackID"] or admin:
            buttons.append(
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit", "emoji": True},
                    "value": str(event["id"]),
                    "action_id": "edit-event",
                }
            )
        # if not user_id == event["fields"]["Leader Slack ID"]:
        #     text = (
        #         ":bell: Interested"
        #         if airtable_user["id"]
        #         not in event["fields"].get("Interested Users", [])
        #         else ":white_check_mark: Going"
        #     )
        #     style_dict = (
        #         {"style": "primary"}
        #         if airtable_user["id"]
        #         not in event["fields"].get("Interested Users", [])
        #         else {}
        #     )

        # Temporarily hiding until I fix
        # buttons.append(
        #     {
        #         "type": "button",
        #         "text": {"type": "plain_text", "text": text, "emoji": True},
        #         "value": str(event["id"]),
        #         "action_id": "rsvp",
        #         **style_dict,
        #     }
        # )
        if event["Approved"]:
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
                    "url": event["CalendarLink"],
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
