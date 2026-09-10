from datetime import datetime
from datetime import timedelta

import pytest

from isabelle.tables import Event
from isabelle.utils.database import DatabaseService
from isabelle.utils.database import make_google_calendar_url

pytestmark = pytest.mark.db

START = datetime(2026, 10, 1, 17, 0, 0)
END = START + timedelta(hours=2)
EVENT_LINK = "https://app.slack.com/huddle/T0266FRGM/C01D7AHKMPF"
RAW_DESCRIPTION = [
    {
        "type": "rich_text_section",
        "elements": [{"type": "text", "text": "Come hang out."}],
    }
]


async def _create(service: DatabaseService, **overrides):
    kwargs = {
        "title": "Test Event",
        "description": "Come hang out.",
        "raw_description": RAW_DESCRIPTION,
        "start_time": START,
        "end_time": END,
        "leader_slack_id": "U0TESTLEADER",
        "leader_name": "Test Leader",
        "event_link": EVENT_LINK,
    }
    kwargs.update(overrides)
    return await service.create_event(**kwargs)


async def test_create_event_persists_a_row(clean_events):
    service = DatabaseService()
    created = await _create(service)
    assert created is not None

    rows = await Event.select().where(Event.Title == "Test Event")
    assert len(rows) == 1
    assert rows[0]["LeaderSlackID"] == "U0TESTLEADER"
    assert rows[0]["Leader"] == "Test Leader"


async def test_new_events_are_unapproved_by_default(clean_events):
    service = DatabaseService()
    await _create(service)

    row = (await Event.select().where(Event.Title == "Test Event"))[0]
    assert row["Approved"] is False
    assert row["Cancelled"] is False


async def test_create_event_generates_a_calendar_link(clean_events):
    service = DatabaseService()
    await _create(service)

    row = (await Event.select().where(Event.Title == "Test Event"))[0]
    expected = make_google_calendar_url(
        title="Test Event",
        description="Come hang out.",
        leader="Test Leader",
        event_link=EVENT_LINK,
        start=START,
        end=END,
    )
    assert row["CalendarLink"] == expected


async def test_create_event_defaults_avatar_to_cachet(clean_events):
    service = DatabaseService()
    await _create(service)

    row = (await Event.select().where(Event.Title == "Test Event"))[0]
    assert "U0TESTLEADER" in row["Avatar"]


async def test_get_all_events_excludes_unapproved(clean_events):
    service = DatabaseService()
    await _create(service, title="Unapproved Event")

    assert await service.get_all_events() == []
    assert len(await service.get_all_events(include_unapproved=True)) == 1
