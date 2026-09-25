import json
from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from isabelle.tables import DigestState
from isabelle.utils import digest
from isabelle.utils.digest import DigestConfig
from isabelle.utils.digest import build_digest
from isabelle.utils.digest import is_posting_day
from isabelle.utils.digest import last_due_at
from isabelle.utils.env import env

RAW_DESCRIPTION = json.dumps(
    {
        "elements": [
            {
                "type": "rich_text_section",
                "elements": [{"type": "text", "text": "Come hang out."}],
            }
        ]
    }
)


def config(**overrides) -> DigestConfig:
    params = {
        "frequency": "weekly",
        "hour": 14,
        "weekday": 0,
        "max_events": 12,
        "repost_after_messages": 15,
    }
    params.update(overrides)
    return DigestConfig(**params)


def event(**overrides) -> dict:
    row = {
        "id": "8a20db4e-35e8-47a3-a075-d392173a86d9",
        "Title": "Code in the Dark",
        "StartTime": datetime(2026, 10, 1, 17, 0, tzinfo=timezone.utc),
        "Leader": "Test Leader",
        "LeaderSlackID": "U0TESTLEADER",
        "Avatar": "https://cachet.hackclub.com/users/U0TESTLEADER/r",
        "CalendarLink": "https://www.google.com/calendar/render?action=TEMPLATE",
        "RawDescription": RAW_DESCRIPTION,
    }
    row.update(overrides)
    return row


class TestIsPostingDay:
    def test_daily_posts_every_day(self):
        daily = config(frequency="daily")
        assert is_posting_day(daily, date(2026, 10, 1))
        assert is_posting_day(daily, date(2026, 10, 2))

    def test_weekly_posts_only_on_its_weekday(self):
        weekly = config(frequency="weekly", weekday=0)
        assert is_posting_day(weekly, date(2026, 10, 5))  # Monday
        assert not is_posting_day(weekly, date(2026, 10, 6))

    def test_biweekly_skips_every_other_match(self):
        biweekly = config(frequency="biweekly", weekday=0)
        mondays = [is_posting_day(biweekly, date(2026, 10, d)) for d in (5, 12, 19, 26)]
        assert mondays.count(True) == 2
        assert mondays[0] != mondays[1]
        assert mondays[0] == mondays[2]

    def test_an_unknown_frequency_never_posts(self):
        # env.py rejects these on boot, so this is the belt to that braces:
        # a frequency that slips through must not post every single day.
        assert not is_posting_day(config(frequency="monthly"), date(2026, 10, 1))


class TestLastDueAt:
    def test_returns_todays_slot_once_the_hour_passes(self):
        daily = config(frequency="daily", hour=14)
        at = datetime(2026, 10, 1, 14, 30, tzinfo=timezone.utc)
        assert last_due_at(daily, at) == datetime(
            2026, 10, 1, 14, 0, tzinfo=timezone.utc
        )

    def test_returns_yesterdays_slot_before_the_hour(self):
        daily = config(frequency="daily", hour=14)
        at = datetime(2026, 10, 1, 13, 59, tzinfo=timezone.utc)
        assert last_due_at(daily, at) == datetime(
            2026, 9, 30, 14, 0, tzinfo=timezone.utc
        )

    def test_weekly_reaches_back_to_its_weekday(self):
        weekly = config(frequency="weekly", weekday=0, hour=14)
        at = datetime(2026, 10, 8, 9, 0, tzinfo=timezone.utc)  # a Thursday
        assert last_due_at(weekly, at) == datetime(
            2026, 10, 5, 14, 0, tzinfo=timezone.utc
        )

    def test_converts_a_non_utc_clock(self):
        daily = config(frequency="daily", hour=14)
        at = datetime(2026, 10, 1, 8, 30, tzinfo=timezone(timedelta(hours=-7)))
        assert last_due_at(daily, at) == datetime(
            2026, 10, 1, 14, 0, tzinfo=timezone.utc
        )


class TestBuildDigest:
    def test_rsvp_button_carries_the_event_id(self):
        # The action_id is the contract with isabelle/events/buttons/rsvp.py.
        # If either side moves, this should fail loudly.
        blocks, _ = build_digest([event()], config())
        actions = next(b for b in blocks if b["type"] == "actions")
        rsvp = next(e for e in actions["elements"] if e.get("action_id") == "rsvp")
        assert rsvp["value"] == "8a20db4e-35e8-47a3-a075-d392173a86d9"

    def test_renders_the_start_time_as_a_slack_date_token(self):
        blocks, _ = build_digest([event()], config())
        section = next(b for b in blocks if b["type"] == "section")
        assert "<!date^1790874000^" in section["text"]["text"]

    def test_includes_the_description(self):
        blocks, _ = build_digest([event()], config())
        section = next(b for b in blocks if b["type"] == "section")
        assert "Come hang out." in section["text"]["text"]

    def test_survives_an_event_with_no_description(self):
        blocks, _ = build_digest([event(RawDescription=None)], config())
        section = next(b for b in blocks if b["type"] == "section")
        assert "Code in the Dark" in section["text"]["text"]

    def test_survives_unparseable_rich_text(self):
        blocks, _ = build_digest([event(RawDescription="{not json")], config())
        section = next(b for b in blocks if b["type"] == "section")
        assert "Code in the Dark" in section["text"]["text"]

    def test_drops_the_gcal_button_when_there_is_no_link(self):
        blocks, _ = build_digest([event(CalendarLink=None)], config())
        actions = next(b for b in blocks if b["type"] == "actions")
        assert [e["action_id"] for e in actions["elements"]] == ["rsvp"]

    def test_caps_the_event_count_and_says_how_many_were_left_out(self):
        events = [event(id=f"evt_{i}") for i in range(20)]
        blocks, _ = build_digest(events, config(max_events=3))
        assert len([b for b in blocks if b["type"] == "section"]) == 3
        assert "And 17 more" in blocks[-1]["elements"][0]["text"]

    def test_stays_under_the_slack_block_limit_at_the_maximum(self):
        # Slack rejects a message over 50 blocks outright, so the cap in
        # env.py is load-bearing rather than cosmetic.
        events = [event(id=f"evt_{i}") for i in range(16)]
        blocks, _ = build_digest(events, config(max_events=16))
        assert len(blocks) <= digest.MAX_BLOCKS


@pytest_asyncio.fixture
async def clean_digest_state():
    await DigestState.delete(force=True)
    yield
    await DigestState.delete(force=True)


@pytest.mark.db
class TestState:
    async def test_seed_state_records_now_without_posting(self, clean_digest_state):
        at = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
        await digest.seed_state(at)
        state = await digest.get_state()
        assert state["last_posted_at"] == at
        assert state["last_checked_at"] == at

    async def test_seed_state_does_not_move_an_existing_row(self, clean_digest_state):
        # A restart must not rewrite the mark, or a redeploy just before a due
        # time would push the digest out by a whole period.
        first = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
        await digest.seed_state(first)
        await digest.seed_state(first + timedelta(days=3))
        assert (await digest.get_state())["last_posted_at"] == first

    async def test_mark_posted_records_the_message_and_line_up(
        self, clean_digest_state
    ):
        await digest.seed_state(datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc))
        later = datetime(2026, 10, 8, 14, 0, tzinfo=timezone.utc)
        await digest.mark_posted(later, "1791219600.000100", ["evt_1", "evt_2"])

        state = await digest.get_state()
        assert state["last_posted_at"] == later
        assert state["last_checked_at"] == later
        assert state["last_message_ts"] == "1791219600.000100"
        assert state["last_event_ids"] == ["evt_1", "evt_2"]
        assert await DigestState.count() == 1

    async def test_mark_checked_leaves_the_last_post_alone(self, clean_digest_state):
        # "dailyish" counts channel messages from the last real post, so a
        # suppressed slot must not move that cursor forward.
        posted = datetime(2026, 10, 1, 14, 0, tzinfo=timezone.utc)
        await digest.mark_posted(posted, "1.0", ["evt_1"])
        await digest.mark_checked(datetime(2026, 10, 2, 14, 0, tzinfo=timezone.utc))

        state = await digest.get_state()
        assert state["last_posted_at"] == posted
        assert state["last_message_ts"] == "1.0"
        assert state["last_checked_at"] == datetime(
            2026, 10, 2, 14, 0, tzinfo=timezone.utc
        )


class TestNaiveStartTimes:
    def test_reads_a_naive_start_time_as_utc(self):
        # Event.StartTime is a naive Timestamp column, so without pinning the
        # timezone the rendered time moves with the container's TZ.
        naive = datetime(2026, 10, 1, 17, 0)
        aware = datetime(2026, 10, 1, 17, 0, tzinfo=timezone.utc)

        naive_blocks, _ = build_digest([event(StartTime=naive)], config())
        aware_blocks, _ = build_digest([event(StartTime=aware)], config())

        assert naive_blocks == aware_blocks


@pytest.mark.db
class TestDailyish:
    """The "dailyish" frequency: daily, but quiet about repeats.

    It comes up for consideration every day. It posts when the line-up changed,
    or when an unchanged line-up has been buried under enough channel messages
    to be worth repeating. Otherwise it stays silent.
    """

    AT = datetime(2026, 10, 2, 14, 30, tzinfo=timezone.utc)

    @pytest_asyncio.fixture(autouse=True)
    async def _dailyish_env(self, clean_digest_state, monkeypatch):
        monkeypatch.setattr(env, "digest_channel", "C0TESTDIGEST")
        monkeypatch.setattr(env, "digest_frequency", "dailyish")
        monkeypatch.setattr(env, "digest_hour", 14)
        monkeypatch.setattr(env, "digest_repost_after_messages", 15)

        self.post = AsyncMock(return_value={"ok": True, "ts": "200.0"})
        monkeypatch.setattr(digest.client, "chat_postMessage", self.post)

        self.history = AsyncMock(return_value={"messages": []})
        monkeypatch.setattr(digest.client, "conversations_history", self.history)

    def _events(self, *ids):
        return [event(id=i) for i in ids]

    def _database(self, events):
        database = type("FakeDatabase", (), {})()

        async def get_upcoming_events(include_unapproved=False):
            return events

        database.get_upcoming_events = get_upcoming_events
        return database

    async def _run(self, monkeypatch, events, at=None, force=False):
        monkeypatch.setattr(env, "database", self._database(events))
        return await digest.maybe_post_digest(at=at or self.AT, force=force)

    async def test_posts_when_there_is_no_previous_digest(self, monkeypatch):
        assert await self._run(monkeypatch, self._events("evt_1")) is True
        assert self.post.await_count == 1

    async def test_stays_quiet_when_the_line_up_is_unchanged(self, monkeypatch):
        await digest.mark_posted(
            self.AT - timedelta(days=1), "100.0", ["evt_1", "evt_2"]
        )
        self.history.return_value = {"messages": [{"ts": "1"}] * 3}

        assert await self._run(monkeypatch, self._events("evt_1", "evt_2")) is False
        self.post.assert_not_awaited()

    async def test_posts_when_a_new_event_appears(self, monkeypatch):
        await digest.mark_posted(self.AT - timedelta(days=1), "100.0", ["evt_1"])
        self.history.return_value = {"messages": []}

        assert await self._run(monkeypatch, self._events("evt_1", "evt_2")) is True
        assert self.post.await_count == 1
        # A quiet channel is no obstacle when there is something new to say.
        self.history.assert_not_awaited()

    async def test_posts_when_an_event_drops_off(self, monkeypatch):
        await digest.mark_posted(
            self.AT - timedelta(days=1), "100.0", ["evt_1", "evt_2"]
        )

        assert await self._run(monkeypatch, self._events("evt_1")) is True
        assert self.post.await_count == 1

    async def test_reposts_an_unchanged_line_up_once_it_is_buried(self, monkeypatch):
        await digest.mark_posted(self.AT - timedelta(days=1), "100.0", ["evt_1"])
        self.history.return_value = {"messages": [{"ts": "1"}] * 15}

        assert await self._run(monkeypatch, self._events("evt_1")) is True
        assert self.post.await_count == 1
        assert self.history.await_args.kwargs["oldest"] == "100.0"
        assert self.history.await_args.kwargs["inclusive"] is False

    async def test_one_message_short_of_the_threshold_stays_quiet(self, monkeypatch):
        await digest.mark_posted(self.AT - timedelta(days=1), "100.0", ["evt_1"])
        self.history.return_value = {"messages": [{"ts": "1"}] * 14}

        assert await self._run(monkeypatch, self._events("evt_1")) is False
        self.post.assert_not_awaited()

    async def test_a_suppressed_day_does_not_move_the_message_cursor(self, monkeypatch):
        # Otherwise every quiet day resets the count and the digest can never
        # accumulate enough messages to resurface.
        posted_at = self.AT - timedelta(days=1)
        await digest.mark_posted(posted_at, "100.0", ["evt_1"])
        self.history.return_value = {"messages": [{"ts": "1"}] * 2}

        await self._run(monkeypatch, self._events("evt_1"))

        state = await digest.get_state()
        assert state["last_posted_at"] == posted_at
        assert state["last_message_ts"] == "100.0"
        assert state["last_checked_at"] == self.AT

    async def test_a_suppressed_day_is_not_reconsidered_that_same_day(
        self, monkeypatch
    ):
        await digest.mark_posted(self.AT - timedelta(days=1), "100.0", ["evt_1"])
        self.history.return_value = {"messages": [{"ts": "1"}] * 2}

        await self._run(monkeypatch, self._events("evt_1"))
        # The worker ticks every 60 seconds; the slot is spent.
        await self._run(
            monkeypatch, self._events("evt_1"), at=self.AT + timedelta(minutes=1)
        )

        assert self.history.await_count == 1
        self.post.assert_not_awaited()

    async def test_a_failing_history_read_does_not_repost(self, monkeypatch):
        # Erring toward silence: a Slack outage should not turn into a repeat
        # of yesterday's message.
        await digest.mark_posted(self.AT - timedelta(days=1), "100.0", ["evt_1"])
        self.history.side_effect = RuntimeError("slack is down")

        assert await self._run(monkeypatch, self._events("evt_1")) is False
        self.post.assert_not_awaited()

    async def test_an_unknown_last_message_does_not_repost(self, monkeypatch):
        # Nothing to measure from, so there is no evidence it is buried.
        await digest.mark_posted(self.AT - timedelta(days=1), None, ["evt_1"])

        assert await self._run(monkeypatch, self._events("evt_1")) is False
        self.history.assert_not_awaited()

    async def test_force_ignores_both_the_slot_and_the_repeat_check(self, monkeypatch):
        await digest.mark_posted(self.AT, "100.0", ["evt_1"])

        assert await self._run(monkeypatch, self._events("evt_1"), force=True) is True
        assert self.post.await_count == 1

    async def test_only_the_shown_slice_counts_as_the_line_up(self, monkeypatch):
        # An event past the cap changes nothing a reader would see, so it is
        # not a reason to repeat the message.
        monkeypatch.setattr(env, "digest_max_events", 2)
        await digest.mark_posted(
            self.AT - timedelta(days=1), "100.0", ["evt_1", "evt_2"]
        )
        self.history.return_value = {"messages": []}

        assert (
            await self._run(monkeypatch, self._events("evt_1", "evt_2", "evt_3"))
            is False
        )
        self.post.assert_not_awaited()

    async def test_daily_is_unaffected_by_the_repeat_rule(self, monkeypatch):
        # "daily" keeps its old behaviour: same events, post anyway.
        monkeypatch.setattr(env, "digest_frequency", "daily")
        await digest.mark_posted(self.AT - timedelta(days=1), "100.0", ["evt_1"])

        assert await self._run(monkeypatch, self._events("evt_1")) is True
        assert self.post.await_count == 1
        self.history.assert_not_awaited()
