from datetime import datetime
from datetime import timedelta
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from isabelle.events.buttons.rsvp import handle_rsvp_btn
from isabelle.utils.database import DatabaseService

pytestmark = pytest.mark.db

START = datetime(2026, 10, 1, 17, 0, 0)
RAW_DESCRIPTION = [
    {
        "type": "rich_text_section",
        "elements": [{"type": "text", "text": "Come hang out."}],
    }
]


async def _create_approved_event(service: DatabaseService):
    return await service.create_event(
        title="Button RSVP Test",
        description="Come hang out.",
        raw_description=RAW_DESCRIPTION,
        start_time=START,
        end_time=START + timedelta(hours=2),
        leader_slack_id="U0TESTLEADER",
        leader_name="Test Leader",
        event_link="https://app.slack.com/huddle/T0266FRGM/C01D7AHKMPF",
        approved=True,
    )


def _fake_client(dm_texts: list[str]):
    client = AsyncMock()
    client.chat_postMessage = AsyncMock(
        side_effect=lambda **kw: dm_texts.append(kw["text"]) or {"ok": True}
    )
    client.views_publish = AsyncMock(return_value={"ok": True})
    return client


async def _click_rsvp(event_id: str, user_id: str) -> list[str]:
    dm_texts: list[str] = []
    with patch("isabelle.events.buttons.rsvp.get_home", new=AsyncMock(return_value={})):
        await handle_rsvp_btn(
            AsyncMock(),
            {"user": {"id": user_id}, "actions": [{"value": event_id}]},
            _fake_client(dm_texts),
        )
    return dm_texts


async def test_rsvp_click_confirms_interest(clean_events):
    # RSVPs are written to RSVPData, not the legacy InterestedUsers array.
    # The confirmation DM must reflect RSVPData or every click reads as an
    # un-RSVP (see bf1e1a6, which fixed the same bug in the reaction path).
    service = DatabaseService()
    event = await _create_approved_event(service)

    dm_texts = await _click_rsvp(str(event.id), "U0CLICKER")

    assert any("interested in" in t and "no longer" not in t for t in dm_texts)
    assert not any("no longer interested" in t for t in dm_texts)


async def test_second_rsvp_click_confirms_uninterest(clean_events):
    service = DatabaseService()
    event = await _create_approved_event(service)

    await _click_rsvp(str(event.id), "U0CLICKER")
    dm_texts = await _click_rsvp(str(event.id), "U0CLICKER")

    assert any("no longer interested" in t for t in dm_texts)


WEB_USER = {"sub": "sub-web-1", "name": "Web User", "email": "web@example.com"}


async def test_clicking_after_a_website_rsvp_removes_it_instead_of_doubling_it(
    clean_events,
):
    service = DatabaseService()
    event = await _create_approved_event(service)
    event_id = str(event.id)
    await service.toggle_user_interest(
        event_id, "U0WEBUSER", forced_state=True, user_info=WEB_USER
    )

    dm_texts = await _click_rsvp(event_id, "U0WEBUSER")

    assert any("no longer interested" in t for t in dm_texts)
    stored = await service.get_event(event_id)
    assert stored["InterestCount"] == 0
    assert stored["RSVPData"] == {}


async def test_a_slack_rsvp_then_a_website_rsvp_counts_once(clean_events):
    service = DatabaseService()
    event = await _create_approved_event(service)
    event_id = str(event.id)

    await _click_rsvp(event_id, "U0WEBUSER")
    await service.toggle_user_interest(
        event_id, "U0WEBUSER", forced_state=True, user_info=WEB_USER
    )

    stored = await service.get_event(event_id)
    assert stored["InterestCount"] == 1
    assert list(stored["RSVPData"]) == ["sub-web-1"]


async def test_a_forced_slack_rsvp_keeps_an_existing_website_rsvp(clean_events):
    service = DatabaseService()
    event = await _create_approved_event(service)
    event_id = str(event.id)
    await service.toggle_user_interest(
        event_id, "U0WEBUSER", forced_state=True, user_info=WEB_USER
    )

    await service.toggle_user_interest(event_id, "U0WEBUSER", forced_state=True)

    stored = await service.get_event(event_id)
    assert stored["InterestCount"] == 1
    assert stored["RSVPData"]["sub-web-1"]["email"] == "web@example.com"
