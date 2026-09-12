import json
import logging
import secrets
from datetime import datetime
from datetime import timezone

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from isabelle.authz import can_edit_event
from isabelle.authz import can_submit
from isabelle.authz import can_reassign_leader
from isabelle.authz import is_reviewer
from isabelle.tables import Event
from isabelle.tables import Submitter
from isabelle.utils.database import get_cachet_pfp
from isabelle.utils.env import env
from isabelle.utils.notify import notify_attendees_cancelled
from isabelle.utils.notify import notify_event_approved
from isabelle.utils.notify import notify_event_cancelled
from isabelle.utils.notify import notify_event_edited
from isabelle.utils.rich_text import column_to_markdown
from isabelle.utils.rich_text import from_rich_text_column
from isabelle.utils.slack import app
from isabelle.web_submission import as_rich_text
from isabelle.web_submission import validate

MAX_REASON = 2000
MAX_PENDING_PER_SUBMITTER = 5

LIST_COLUMNS = (
    "id",
    "Title",
    "Description",
    "StartTime",
    "EndTime",
    "LeaderSlackID",
    "Leader",
    "Avatar",
    "EventLink",
    "RSVPFormURL",
    "Tags",
    "Approved",
    "Cancelled",
    "CancellationType",
    "RawCancellation",
    "InterestCount",
    "CalendarLink",
    "Calculation",
)


def _unauthorized():
    return JSONResponse({"error": "unauthorized"}, status_code=401)


def _forbidden(message="forbidden"):
    return JSONResponse({"error": message}, status_code=403)


def _not_found():
    return JSONResponse({"error": "event not found"}, status_code=404)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _check_secret(req: Request) -> bool:
    provided = req.headers.get("x-internal-secret", "")
    return secrets.compare_digest(provided, env.events_rsvp_secret)


async def _body(req: Request):
    try:
        return await req.json()
    except Exception:
        return None


def serialise(event) -> dict:
    return {
        "id": str(event.get("id")),
        "title": event.get("Title"),
        "description": event.get("Description"),
        "startTime": _utc_iso(event.get("StartTime")),
        "endTime": _utc_iso(event.get("EndTime")),
        "leaderSlackId": event.get("LeaderSlackID"),
        "leader": event.get("Leader"),
        "avatar": event.get("Avatar"),
        "eventLink": event.get("EventLink"),
        "rsvpFormUrl": event.get("RSVPFormURL"),
        "tags": event.get("Tags") or [],
        "approved": bool(event.get("Approved")),
        "cancelled": bool(event.get("Cancelled")),
        "cancellationType": event.get("CancellationType") or None,
        "cancellationReason": column_to_markdown(event.get("RawCancellation")),
        "interestCount": event.get("InterestCount") or 0,
        "calendarLink": event.get("CalendarLink"),
        "slug": event.get("Calculation"),
    }


def _utc_iso(value):
    if not value:
        return None
    return value.isoformat() + "Z"


def _attendee_slack_ids(event) -> list:
    rsvp_data = event.get("RSVPData") or {}
    if not isinstance(rsvp_data, dict):
        return []
    ids = [v.get("slackId") for v in rsvp_data.values() if isinstance(v, dict)]
    legacy = event.get("InterestedUsers") or []
    return list(dict.fromkeys([i for i in ids + list(legacy) if i]))


async def approve_event(req: Request):
    if not _check_secret(req):
        return _unauthorized()

    body = await _body(req)
    if body is None:
        return JSONResponse({"error": "invalid json"}, status_code=400)

    actor = (body.get("actor_slack_id") or "").strip()
    if not actor:
        return JSONResponse({"error": "actor_slack_id is required"}, status_code=422)

    if not is_reviewer(actor):
        return _forbidden()

    event_id = req.path_params["event_id"]
    event = await env.database.get_event(event_id)
    if not event:
        return _not_found()

    if event.get("Cancelled"):
        return JSONResponse({"error": "event is cancelled"}, status_code=409)
    if event.get("Approved"):
        return JSONResponse({"error": "already approved"}, status_code=409)

    updated = await env.database.update_event(event_id, Approved=True)
    if not updated:
        return JSONResponse({"error": "could not approve event"}, status_code=500)

    await notify_event_approved(updated, actor)

    return JSONResponse(serialise(updated))


async def cancel_event(req: Request):
    if not _check_secret(req):
        return _unauthorized()

    body = await _body(req)
    if body is None:
        return JSONResponse({"error": "invalid json"}, status_code=400)

    actor = (body.get("actor_slack_id") or "").strip()
    if not actor:
        return JSONResponse({"error": "actor_slack_id is required"}, status_code=422)

    if not is_reviewer(actor):
        return _forbidden()

    reason = (body.get("reason") or "").strip()
    if not reason:
        return JSONResponse(
            {"error": "invalid submission", "errors": {"reason": "reason is required"}},
            status_code=422,
        )
    if len(reason) > MAX_REASON:
        return JSONResponse(
            {
                "error": "invalid submission",
                "errors": {"reason": f"reason must be under {MAX_REASON} characters"},
            },
            status_code=422,
        )

    event_id = req.path_params["event_id"]
    event = await env.database.get_event(event_id)
    if not event:
        return _not_found()

    if event.get("Cancelled"):
        return JSONResponse({"error": "already cancelled"}, status_code=409)

    kind = body.get("kind")
    if kind not in ("rejected", "cancelled"):
        kind = "cancelled" if event.get("Approved") else "rejected"

    was_public = bool(event.get("Approved"))
    attendees = _attendee_slack_ids(event) if was_public else []

    updated = await env.database.cancel_event(event_id, reason=reason, kind=kind)
    if not updated:
        return JSONResponse({"error": "could not cancel event"}, status_code=500)

    reason_block = from_rich_text_column(updated.get("RawCancellation"))
    await notify_event_cancelled(updated, actor, reason_block, kind=kind)

    if kind == "cancelled" and attendees:
        await notify_attendees_cancelled(updated, attendees, reason)

    return JSONResponse(serialise(updated))


async def edit_event(req: Request):
    if not _check_secret(req):
        return _unauthorized()

    body = await _body(req)
    if body is None:
        return JSONResponse({"error": "invalid json"}, status_code=400)

    actor = (body.get("actor_slack_id") or "").strip()
    if not actor:
        return JSONResponse({"error": "actor_slack_id is required"}, status_code=422)

    event_id = req.path_params["event_id"]
    event = await env.database.get_event(event_id)
    if not event:
        return _not_found()

    if not can_edit_event(actor, event):
        return _forbidden()

    if event.get("Cancelled"):
        return JSONResponse({"error": "event is cancelled"}, status_code=409)

    requested_leader = (body.get("leader_slack_id") or "").strip()
    current_leader = event.get("LeaderSlackID")
    if requested_leader and requested_leader != current_leader:
        if not can_reassign_leader(actor):
            return _forbidden("only reviewers can reassign the event leader")
    else:
        requested_leader = current_leader

    errors, values = validate(
        {**body, "leader_slack_id": requested_leader}, env.event_tags
    )
    if errors:
        return JSONResponse(
            {"error": "invalid submission", "errors": errors}, status_code=422
        )

    updates = {
        "Title": values["title"],
        "Description": values["description"],
        "RawDescription": json.dumps(
            {"type": "rich_text", "elements": as_rich_text(values["description"])}
        ),
        "StartTime": values["start_time"],
        "EndTime": values["end_time"],
        "EventLink": values["event_link"],
        "RSVPFormURL": values["rsvp_form_url"],
        "Tags": values["tags"],
    }

    if requested_leader != current_leader:
        leader_name = event.get("Leader")
        try:
            slack_user = await app._async_client.users_info(user=requested_leader)
            profile = slack_user["user"]["profile"]
            leader_name = (
                profile.get("real_name") or profile.get("display_name") or leader_name
            )
        except Exception as error:
            logging.warning(
                "Could not resolve Slack name for %s: %s", requested_leader, error
            )
        updates["LeaderSlackID"] = requested_leader
        updates["Leader"] = leader_name
        updates["Avatar"] = get_cachet_pfp(requested_leader)

    updated = await env.database.update_event(event_id, **updates)
    if not updated:
        return JSONResponse({"error": "could not update event"}, status_code=500)

    await notify_event_edited(updated, actor)

    return JSONResponse(serialise(updated))


async def get_manageable_event(req: Request):
    if not _check_secret(req):
        return _unauthorized()

    actor = (req.query_params.get("actor_slack_id") or "").strip()
    if not actor:
        return JSONResponse({"error": "actor_slack_id is required"}, status_code=422)

    event = await env.database.get_event(req.path_params["event_id"])
    if not event:
        return _not_found()

    if not can_edit_event(actor, event):
        return _forbidden()

    return JSONResponse(serialise(event))


async def list_events(req: Request):
    if not _check_secret(req):
        return _unauthorized()

    actor = (req.query_params.get("actor_slack_id") or "").strip()
    if not actor:
        return JSONResponse({"error": "actor_slack_id is required"}, status_code=422)

    scope = req.query_params.get("scope", "mine")
    if scope not in ("mine", "pending"):
        return JSONResponse({"error": "unknown scope"}, status_code=422)

    columns = [getattr(Event, name) for name in LIST_COLUMNS]
    query = Event.select(*columns)

    if scope == "mine":
        query = query.where(Event.LeaderSlackID == actor)
    else:
        if not is_reviewer(actor):
            return _forbidden()
        query = query.where(Event.Approved == False, Event.Cancelled == False)
        if req.query_params.get("include_past") != "true":
            query = query.where(Event.EndTime >= _now())

    rows = await query.order_by(Event.StartTime).output(load_json=True)

    return JSONResponse({"events": [serialise(row) for row in rows]})


async def allowlisted_ids() -> list:
    rows = await Submitter.select(Submitter.SlackID)
    return [row["SlackID"] for row in rows if row.get("SlackID")]


async def may_submit(email, slack_id) -> bool:
    return can_submit(email, slack_id, await allowlisted_ids())


async def pending_submission_count(slack_id) -> int:
    rows = await Event.select(Event.id).where(
        Event.LeaderSlackID == slack_id,
        Event.Approved == False,
        Event.Cancelled == False,
    )
    return len(rows)


async def list_submitters(req: Request):
    if not _check_secret(req):
        return _unauthorized()

    actor = (req.query_params.get("actor_slack_id") or "").strip()
    if not actor:
        return JSONResponse({"error": "actor_slack_id is required"}, status_code=422)
    if not is_reviewer(actor):
        return _forbidden()

    rows = await Submitter.select().order_by(Submitter.AddedAt, ascending=False)
    return JSONResponse(
        {
            "submitters": [
                {
                    "slackId": r.get("SlackID"),
                    "name": r.get("Name"),
                    "note": r.get("Note"),
                    "addedBySlackId": r.get("AddedBySlackID"),
                    "addedAt": _utc_iso(r.get("AddedAt")),
                }
                for r in rows
            ]
        }
    )


async def add_submitter(req: Request):
    if not _check_secret(req):
        return _unauthorized()

    body = await _body(req)
    if body is None:
        return JSONResponse({"error": "invalid json"}, status_code=400)

    actor = (body.get("actor_slack_id") or "").strip()
    if not actor:
        return JSONResponse({"error": "actor_slack_id is required"}, status_code=422)
    if not is_reviewer(actor):
        return _forbidden()

    slack_id = (body.get("slack_id") or "").strip().upper()
    if not slack_id:
        return JSONResponse(
            {"error": "invalid submission", "errors": {"slack_id": "required"}},
            status_code=422,
        )

    existing = await Submitter.select().where(Submitter.SlackID == slack_id).first()
    if existing:
        return JSONResponse({"error": "already on the list"}, status_code=409)

    await Submitter.insert(
        Submitter(
            SlackID=slack_id,
            Name=(body.get("name") or "").strip() or None,
            Note=(body.get("note") or "").strip() or None,
            AddedBySlackID=actor,
            AddedAt=_now(),
        )
    )

    return JSONResponse({"slackId": slack_id}, status_code=201)


async def remove_submitter(req: Request):
    if not _check_secret(req):
        return _unauthorized()

    actor = (req.query_params.get("actor_slack_id") or "").strip()
    if not actor:
        return JSONResponse({"error": "actor_slack_id is required"}, status_code=422)
    if not is_reviewer(actor):
        return _forbidden()

    slack_id = req.path_params["slack_id"]
    await Submitter.delete().where(Submitter.SlackID == slack_id)
    return JSONResponse({"slackId": slack_id})


async def list_tags(req: Request):
    if not _check_secret(req):
        return _unauthorized()

    rows = await Event.select(Event.Tags, Event.Approved).where(
        Event.Cancelled == False
    )

    counts: dict[str, int] = {}
    approved_counts: dict[str, int] = {}
    for row in rows:
        for tag in row.get("Tags") or []:
            if not tag:
                continue
            counts[tag] = counts.get(tag, 0) + 1
            if row.get("Approved"):
                approved_counts[tag] = approved_counts.get(tag, 0) + 1

    curated = set(env.event_tags)
    for tag in curated:
        counts.setdefault(tag, 0)

    tags = [
        {
            "name": name,
            "count": count,
            "approvedCount": approved_counts.get(name, 0),
            "curated": name in curated,
        }
        for name, count in counts.items()
    ]
    tags.sort(key=lambda t: (not t["curated"], -t["count"], t["name"]))

    return JSONResponse({"tags": tags})


async def permissions(req: Request):
    if not _check_secret(req):
        return _unauthorized()

    actor = (req.query_params.get("actor_slack_id") or "").strip()
    if not actor:
        return JSONResponse({"error": "actor_slack_id is required"}, status_code=422)

    return JSONResponse(
        {
            "reviewer": is_reviewer(actor),
            "submitter": await may_submit(req.query_params.get("email"), actor),
        }
    )


routes = [
    Route("/internal/permissions", endpoint=permissions, methods=["GET"]),
    Route("/internal/tags", endpoint=list_tags, methods=["GET"]),
    Route("/internal/submitters", endpoint=list_submitters, methods=["GET"]),
    Route("/internal/submitters", endpoint=add_submitter, methods=["POST"]),
    Route(
        "/internal/submitters/{slack_id}",
        endpoint=remove_submitter,
        methods=["DELETE"],
    ),
    Route("/internal/events/manage", endpoint=list_events, methods=["GET"]),
    Route(
        "/internal/events/{event_id}/approve", endpoint=approve_event, methods=["POST"]
    ),
    Route(
        "/internal/events/{event_id}/cancel", endpoint=cancel_event, methods=["POST"]
    ),
    Route(
        "/internal/events/{event_id}/manage",
        endpoint=get_manageable_event,
        methods=["GET"],
    ),
    Route("/internal/events/{event_id}", endpoint=edit_event, methods=["PATCH"]),
]
