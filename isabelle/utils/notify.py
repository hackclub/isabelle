import logging

from isabelle.utils.env import env
from isabelle.utils.slack import app


async def _safe(coro, description):
    try:
        await coro
    except Exception:
        logging.exception("Could not send Slack message: %s", description)


async def _post(channel, text, blocks=None):
    await _safe(
        app._async_client.chat_postMessage(channel=channel, text=text, blocks=blocks),
        f"post to {channel}",
    )


def _tags(event) -> str:
    tags = event.get("Tags") or []
    return ", ".join(t.replace("-", " ").title() for t in tags) if tags else "None"


async def notify_event_approved(event, actor_slack_id):
    title = event.get("Title")
    leader = event.get("LeaderSlackID")

    await _post(
        env.slack_approval_channel,
        f"<@{actor_slack_id}> approved {title} for <@{leader}>.\nTags: {_tags(event)}",
    )
    if leader:
        await _post(
            leader,
            f"Your event {title} has been approved by <@{actor_slack_id}>! "
            "Please reach out to them if you have any questions or need help.",
        )


async def notify_event_cancelled(event, actor_slack_id, reason_block, kind="cancelled"):
    title = event.get("Title")
    leader = event.get("LeaderSlackID")
    verb = "rejected" if kind == "rejected" else "cancelled"

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<@{actor_slack_id}> {verb} *{title}*.",
            },
        },
        {"type": "divider"},
    ]
    if reason_block:
        blocks.append(reason_block)

    await _post(env.slack_approval_channel, f"{title} was {verb}.", blocks)

    if leader:
        leader_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"Your event *{title}* was {verb} by <@{actor_slack_id}>."
                        if verb == "rejected"
                        else f"Your event *{title}* has been {verb}."
                    ),
                },
            },
            {"type": "divider"},
        ]
        if reason_block:
            leader_blocks.append(reason_block)
        await _post(leader, f"Your event {title} was {verb}.", leader_blocks)


async def notify_attendees_cancelled(event, attendee_slack_ids, reason_markdown):
    title = event.get("Title")
    tail = f"\n\n> {reason_markdown}" if reason_markdown else ""

    for slack_id in attendee_slack_ids:
        if not slack_id:
            continue
        await _post(
            slack_id,
            f"*{title}* has been cancelled, so it will not be going ahead.{tail}",
        )


async def notify_event_edited(event, actor_slack_id):
    title = event.get("Title")
    leader = event.get("LeaderSlackID")

    await _post(
        env.slack_approval_channel,
        f"Event updated by <@{actor_slack_id}>!\n"
        f"*Title:* {title}\n"
        f"*Host:* <@{leader}>\n"
        f"*Tags:* {_tags(event)}\n"
        f"*Start Time:* {event.get('StartTime')}\n"
        f"*End Time:* {event.get('EndTime')}",
    )
