import pytest

from isabelle.authz import can_edit_event
from isabelle.authz import can_submit
from isabelle.authz import can_reassign_leader
from isabelle.authz import is_leader
from isabelle.authz import is_reviewer
from isabelle.utils.env import env

REVIEWER = env.authorised_users[0]
LEADER = "U0LEADER"
STRANGER = "U0STRANGER"

EVENT = {"LeaderSlackID": LEADER}


class TestIsReviewer:
    def test_accepts_a_listed_id(self):
        assert is_reviewer(REVIEWER) is True

    @pytest.mark.parametrize("value", [STRANGER, "", None])
    def test_rejects_anyone_else(self, value):
        assert is_reviewer(value) is False


class TestIsLeader:
    def test_matches_the_event_leader(self):
        assert is_leader(LEADER, EVENT) is True

    def test_rejects_a_different_user(self):
        assert is_leader(STRANGER, EVENT) is False

    @pytest.mark.parametrize(
        "slack_id, event", [(None, EVENT), ("", EVENT), (LEADER, None), (LEADER, {})]
    )
    def test_rejects_missing_inputs(self, slack_id, event):
        assert is_leader(slack_id, event) is False


class TestCanEditEvent:
    def test_leader_can_edit_their_own(self):
        assert can_edit_event(LEADER, EVENT) is True

    def test_reviewer_can_edit_anyones(self):
        assert can_edit_event(REVIEWER, EVENT) is True

    def test_stranger_cannot(self):
        assert can_edit_event(STRANGER, EVENT) is False

    def test_nobody_can_edit_an_event_with_no_leader(self):
        assert can_edit_event(STRANGER, {"LeaderSlackID": None}) is False


class TestCanReassignLeader:
    def test_reviewers_only(self):
        assert can_reassign_leader(REVIEWER) is True
        assert can_reassign_leader(LEADER) is False


class TestCanSubmit:
    def test_a_hack_club_email_may_submit(self):
        assert can_submit("wally@hackclub.com", "U0ANYONE", []) is True

    def test_the_domain_check_ignores_case(self):
        assert can_submit("Wally@HackClub.COM", "U0ANYONE", []) is True

    def test_a_personal_email_may_not(self):
        assert can_submit("someone@gmail.com", "U0ANYONE", []) is False

    def test_a_lookalike_domain_may_not(self):
        for email in ("a@nothackclub.com", "a@hackclub.com.evil.net", "a@hackclub.org"):
            assert can_submit(email, "U0ANYONE", []) is False

    def test_someone_on_the_allowlist_may(self):
        assert can_submit("someone@gmail.com", "U0FRIEND", ["U0FRIEND"]) is True

    def test_reviewers_may_regardless_of_email(self):
        assert can_submit("someone@gmail.com", REVIEWER, []) is True

    @pytest.mark.parametrize("email", [None, "", "not-an-email", 12345])
    def test_a_missing_or_malformed_email_is_not_a_pass(self, email):
        assert can_submit(email, "U0ANYONE", []) is False
