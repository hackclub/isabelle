from datetime import datetime
from datetime import timedelta

import pytest
from starlette.testclient import TestClient

from app import api
from isabelle.tables import Event
from isabelle.tables import Submitter
from isabelle.utils.env import env
from isabelle.utils.rich_text import column_to_markdown

pytestmark = pytest.mark.db

REVIEWER = env.authorised_users[0]
LEADER = "U0LEADER"
STRANGER = "U0STRANGER"

START = datetime.now() + timedelta(days=30)
END = START + timedelta(hours=2)


@pytest.fixture
def client():
    return TestClient(api)


@pytest.fixture
def auth(rsvp_secret):
    return {"x-internal-secret": rsvp_secret}


async def make_event(approved=False, title="Lifecycle event"):
    await env.database.create_event(
        title=title,
        description="Something to do.",
        raw_description=[
            {"type": "rich_text_section", "elements": [{"type": "text", "text": "hi"}]}
        ],
        start_time=START,
        end_time=END,
        leader_slack_id=LEADER,
        leader_name="A Leader",
        event_link="https://example.com/huddle",
        approved=approved,
        tags=["workshop"],
    )
    row = (await Event.select().where(Event.Title == title))[0]
    return str(row["id"])


def edit_body(actor, **overrides):
    body = {
        "actor_slack_id": actor,
        "title": "Renamed event",
        "description": "Edited description.",
        "start_time": START.isoformat(),
        "end_time": END.isoformat(),
        "tags": ["social"],
    }
    body.update(overrides)
    return body


async def test_reviewer_can_approve(client, auth, clean_events):
    event_id = await make_event()

    response = client.post(
        f"/internal/events/{event_id}/approve",
        json={"actor_slack_id": REVIEWER},
        headers=auth,
    )

    assert response.status_code == 200
    assert response.json()["approved"] is True
    row = (await Event.select().where(Event.id == event_id))[0]
    assert row["Approved"] is True


async def test_stranger_cannot_approve_and_row_is_untouched(client, auth, clean_events):
    event_id = await make_event()

    response = client.post(
        f"/internal/events/{event_id}/approve",
        json={"actor_slack_id": STRANGER},
        headers=auth,
    )

    assert response.status_code == 403
    row = (await Event.select().where(Event.id == event_id))[0]
    assert row["Approved"] is False


async def test_cancelling_an_approved_event_is_a_cancellation(
    client, auth, clean_events
):
    event_id = await make_event(approved=True)

    response = client.post(
        f"/internal/events/{event_id}/cancel",
        json={"actor_slack_id": REVIEWER, "reason": "Venue fell through."},
        headers=auth,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["cancellationType"] == "cancelled"
    assert body["cancellationReason"] == "Venue fell through."

    row = (await Event.select().where(Event.id == event_id))[0]
    assert row["Cancelled"] is True
    assert row["Approved"] is False
    assert column_to_markdown(row["RawCancellation"]) == "Venue fell through."


async def test_cancelling_an_unapproved_event_is_a_rejection(
    client, auth, clean_events
):
    event_id = await make_event(approved=False)

    response = client.post(
        f"/internal/events/{event_id}/cancel",
        json={"actor_slack_id": REVIEWER, "reason": "Clashes with another event."},
        headers=auth,
    )

    assert response.json()["cancellationType"] == "rejected"


async def test_cancelling_twice_conflicts(client, auth, clean_events):
    event_id = await make_event(approved=True)
    payload = {"actor_slack_id": REVIEWER, "reason": "Called off."}

    client.post(f"/internal/events/{event_id}/cancel", json=payload, headers=auth)
    second = client.post(
        f"/internal/events/{event_id}/cancel", json=payload, headers=auth
    )

    assert second.status_code == 409


async def test_leader_can_edit_their_own_unapproved_event(client, auth, clean_events):
    event_id = await make_event(approved=False)

    response = client.patch(
        f"/internal/events/{event_id}", json=edit_body(LEADER), headers=auth
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Renamed event"


async def test_stranger_cannot_edit_and_row_is_untouched(client, auth, clean_events):
    event_id = await make_event()

    response = client.patch(
        f"/internal/events/{event_id}", json=edit_body(STRANGER), headers=auth
    )

    assert response.status_code == 403
    row = (await Event.select().where(Event.id == event_id))[0]
    assert row["Title"] == "Lifecycle event"


async def test_only_reviewers_may_reassign_the_leader(client, auth, clean_events):
    event_id = await make_event()

    denied = client.patch(
        f"/internal/events/{event_id}",
        json=edit_body(LEADER, leader_slack_id=STRANGER),
        headers=auth,
    )
    assert denied.status_code == 403

    row = (await Event.select().where(Event.id == event_id))[0]
    assert row["LeaderSlackID"] == LEADER


async def test_renaming_refreshes_the_calendar_link_and_slug(
    client, auth, clean_events
):
    event_id = await make_event()

    client.patch(f"/internal/events/{event_id}", json=edit_body(LEADER), headers=auth)

    row = (await Event.select().where(Event.id == event_id))[0]
    assert "Renamed" in row["CalendarLink"]
    assert row["Calculation"] == "renamed-event"


async def test_mine_scope_returns_own_events_in_every_state(client, auth, clean_events):
    await make_event(approved=False, title="Mine pending")
    await make_event(approved=True, title="Mine live")

    response = client.get(
        "/internal/events/manage",
        params={"actor_slack_id": LEADER, "scope": "mine"},
        headers=auth,
    )

    titles = {e["title"] for e in response.json()["events"]}
    assert titles == {"Mine pending", "Mine live"}


async def test_mine_scope_excludes_other_peoples_events(client, auth, clean_events):
    await make_event(title="Not yours")

    response = client.get(
        "/internal/events/manage",
        params={"actor_slack_id": STRANGER, "scope": "mine"},
        headers=auth,
    )

    assert response.json()["events"] == []


async def test_listings_never_leak_rsvp_data(client, auth, clean_events):
    await make_event()

    response = client.get(
        "/internal/events/manage",
        params={"actor_slack_id": LEADER, "scope": "mine"},
        headers=auth,
    )

    assert "RSVPData" not in response.text
    assert "InterestedUsers" not in response.text


async def test_pending_scope_excludes_approved_and_cancelled(
    client, auth, clean_events
):
    await make_event(approved=False, title="Waiting")
    await make_event(approved=True, title="Already live")

    response = client.get(
        "/internal/events/manage",
        params={"actor_slack_id": REVIEWER, "scope": "pending"},
        headers=auth,
    )

    titles = {e["title"] for e in response.json()["events"]}
    assert titles == {"Waiting"}


async def test_slack_failure_does_not_fail_the_write(
    client, auth, clean_events, monkeypatch
):
    event_id = await make_event()

    async def explode(*args, **kwargs):
        raise RuntimeError("slack is down")

    monkeypatch.setattr(
        "isabelle.utils.notify.app._async_client.chat_postMessage", explode
    )

    response = client.post(
        f"/internal/events/{event_id}/approve",
        json={"actor_slack_id": REVIEWER},
        headers=auth,
    )

    assert response.status_code == 200
    row = (await Event.select().where(Event.id == event_id))[0]
    assert row["Approved"] is True


async def test_timestamps_are_marked_as_utc(client, auth, clean_events):
    event_id = await make_event()

    response = client.get(
        f"/internal/events/{event_id}/manage",
        params={"actor_slack_id": LEADER},
        headers=auth,
    )

    body = response.json()
    assert body["startTime"].endswith("Z")
    assert body["endTime"].endswith("Z")


@pytest.fixture
async def clean_submitters():
    await Submitter.delete(force=True)
    yield
    await Submitter.delete(force=True)


async def test_adding_a_submitter_writes_a_row(client, auth, clean_submitters):
    response = client.post(
        "/internal/submitters",
        json={
            "actor_slack_id": REVIEWER,
            "slack_id": "U0FRIEND",
            "name": "A Friend",
            "note": "Runs the weekly CTF",
        },
        headers=auth,
    )

    assert response.status_code == 201
    rows = await Submitter.select().where(Submitter.SlackID == "U0FRIEND")
    assert len(rows) == 1
    assert rows[0]["Name"] == "A Friend"
    assert rows[0]["AddedBySlackID"] == REVIEWER


async def test_an_added_submitter_may_then_submit(client, auth, clean_submitters):
    client.post(
        "/internal/submitters",
        json={"actor_slack_id": REVIEWER, "slack_id": "U0FRIEND"},
        headers=auth,
    )

    response = client.get(
        "/internal/permissions",
        params={"actor_slack_id": "U0FRIEND", "email": "someone@gmail.com"},
        headers=auth,
    )

    assert response.json()["submitter"] is True


async def test_a_personal_email_alone_is_not_enough(client, auth, clean_submitters):
    response = client.get(
        "/internal/permissions",
        params={"actor_slack_id": "U0STRANGER", "email": "someone@gmail.com"},
        headers=auth,
    )

    assert response.json()["submitter"] is False


async def test_adding_the_same_person_twice_conflicts(client, auth, clean_submitters):
    payload = {"actor_slack_id": REVIEWER, "slack_id": "U0FRIEND"}

    first = client.post("/internal/submitters", json=payload, headers=auth)
    second = client.post("/internal/submitters", json=payload, headers=auth)

    assert first.status_code == 201
    assert second.status_code == 409
    assert len(await Submitter.select()) == 1


async def test_removing_a_submitter_revokes_access(client, auth, clean_submitters):
    client.post(
        "/internal/submitters",
        json={"actor_slack_id": REVIEWER, "slack_id": "U0FRIEND"},
        headers=auth,
    )

    response = client.delete(
        "/internal/submitters/U0FRIEND",
        params={"actor_slack_id": REVIEWER},
        headers=auth,
    )

    assert response.status_code == 200
    assert await Submitter.select().where(Submitter.SlackID == "U0FRIEND") == []


async def test_a_non_reviewer_cannot_add_anyone(client, auth, clean_submitters):
    response = client.post(
        "/internal/submitters",
        json={"actor_slack_id": STRANGER, "slack_id": "U0SNEAKY"},
        headers=auth,
    )

    assert response.status_code == 403
    assert await Submitter.select() == []


async def test_a_non_reviewer_cannot_remove_anyone(client, auth, clean_submitters):
    client.post(
        "/internal/submitters",
        json={"actor_slack_id": REVIEWER, "slack_id": "U0FRIEND"},
        headers=auth,
    )

    response = client.delete(
        "/internal/submitters/U0FRIEND",
        params={"actor_slack_id": STRANGER},
        headers=auth,
    )

    assert response.status_code == 403
    assert len(await Submitter.select()) == 1


async def test_submission_is_refused_without_permission(client, auth, clean_events, clean_submitters):
    response = client.post(
        "/internal/events",
        json={
            "title": "Sneaky event",
            "description": "Submitted by someone with no permission.",
            "start_time": START.isoformat(),
            "end_time": END.isoformat(),
            "leader_slack_id": "U0STRANGER",
            "submitted_by": {"email": "someone@gmail.com"},
        },
        headers=auth,
    )

    assert response.status_code == 403
    assert await Event.select().where(Event.Title == "Sneaky event") == []


async def test_submission_is_allowed_with_a_hack_club_email(
    client, auth, clean_events, clean_submitters
):
    response = client.post(
        "/internal/events",
        json={
            "title": "Staff event",
            "description": "Submitted by someone on staff.",
            "start_time": START.isoformat(),
            "end_time": END.isoformat(),
            "leader_slack_id": "U0STAFF",
            "submitted_by": {"email": "wally@hackclub.com"},
        },
        headers=auth,
    )

    assert response.status_code == 201
    assert len(await Event.select().where(Event.Title == "Staff event")) == 1
