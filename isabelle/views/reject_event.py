from isabelle.utils.env import env


async def get_reject_event_modal(event_id: str):
    event = await env.database.get_event(event_id)
    if not event:
        return {
            "type": "modal",
            "title": {"type": "plain_text", "text": "Error", "emoji": True},
            "close": {"type": "plain_text", "text": "Close", "emoji": True},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Event with id `{event_id}` not found.",
                    },
                }
            ],
        }
    return {
        "type": "modal",
        "callback_id": "reject_event",
        "title": {"type": "plain_text", "text": "Reject Event", "emoji": True},
        "submit": {"type": "plain_text", "text": "Reject", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "blocks": [
            {
                "type": "input",
                "block_id": "message",
                "element": {"type": "rich_text_input", "action_id": "message"},
                "label": {
                    "type": "plain_text",
                    "text": f'Why are you rejecting "{event["Title"]}"?',
                    "emoji": True,
                },
            }
        ],
        "private_metadata": event_id,
    }
