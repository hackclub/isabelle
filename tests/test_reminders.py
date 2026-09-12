from datetime import datetime
from datetime import timedelta

import pytest

from isabelle.reminders import DAY
from isabelle.reminders import HOUR
from isabelle.reminders import STARTING
from isabelle.reminders import due_reminder
from isabelle.reminders import flags_to_set
from isabelle.reminders import message_for

NOW = datetime(2026, 10, 1, 12, 0, 0)


def event(starts_in, **overrides):
    payload = {
        "Title": "Code in the Dark",
        "Leader": "amogh",
        "EventLink": "https://app.slack.com/huddle/x",
        "StartTime": NOW + starts_in,
        "Approved": True,
        "Cancelled": False,
        "Sent1DayReminder": False,
        "Sent1HourReminder": False,
        "SentStartingReminder": False,
    }
    payload.update(overrides)
    return payload


class TestDueReminder:
    def test_a_day_out(self):
        assert due_reminder(event(timedelta(hours=20)), NOW) == DAY

    def test_an_hour_out(self):
        assert due_reminder(event(timedelta(minutes=45)), NOW) == HOUR

    def test_right_as_it_starts(self):
        assert due_reminder(event(timedelta(0)), NOW) == STARTING

    def test_already_started(self):
        assert due_reminder(event(timedelta(minutes=-5)), NOW) == STARTING

    def test_too_far_out_to_remind(self):
        assert due_reminder(event(timedelta(days=3)), NOW) is None

    @pytest.mark.parametrize(
        "starts_in, flag",
        [
            (timedelta(hours=20), "Sent1DayReminder"),
            (timedelta(minutes=45), "Sent1HourReminder"),
            (timedelta(minutes=-5), "SentStartingReminder"),
        ],
    )
    def test_never_sends_the_same_reminder_twice(self, starts_in, flag):
        assert due_reminder(event(starts_in, **{flag: True}), NOW) is None

    def test_an_unapproved_event_is_never_announced(self):
        assert due_reminder(event(timedelta(minutes=45), Approved=False), NOW) is None

    def test_a_cancelled_event_is_never_announced(self):
        assert due_reminder(event(timedelta(minutes=45), Cancelled=True), NOW) is None

    def test_an_event_with_no_start_is_skipped(self):
        assert due_reminder(event(timedelta(0), StartTime=None), NOW) is None

    def test_a_late_submission_gets_the_urgent_reminder_not_the_wrong_one(self):
        assert due_reminder(event(timedelta(minutes=30)), NOW) == HOUR


class TestFlagsToSet:
    def test_sending_the_starting_one_retires_the_earlier_ones(self):
        assert flags_to_set(STARTING) == {
            "Sent1DayReminder": True,
            "Sent1HourReminder": True,
            "SentStartingReminder": True,
        }

    def test_sending_the_hour_one_retires_the_day_one(self):
        assert flags_to_set(HOUR) == {
            "Sent1DayReminder": True,
            "Sent1HourReminder": True,
        }

    def test_an_event_reminded_late_never_says_tomorrow_afterwards(self):
        after = event(timedelta(minutes=30), **flags_to_set(HOUR))
        assert due_reminder(after, NOW) is None


class TestMessages:
    def test_the_hour_and_starting_messages_carry_the_link(self):
        for kind in (HOUR, STARTING):
            assert "https://app.slack.com/huddle/x" in message_for(
                kind, event(timedelta(0))
            )

    def test_a_missing_link_falls_back_rather_than_printing_none(self):
        message = message_for(STARTING, event(timedelta(0), EventLink=None))
        assert "None" not in message
        assert "the Slack" in message

    def test_the_starting_message_says_it_is_starting(self):
        assert "starting now" in message_for(STARTING, event(timedelta(0)))
