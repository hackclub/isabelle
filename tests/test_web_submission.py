from datetime import datetime

import pytest
from starlette.testclient import TestClient

from app import api
from isabelle.web_submission import DEFAULT_EVENT_LINK
from isabelle.web_submission import MAX_TITLE
from isabelle.web_submission import as_rich_text
from isabelle.web_submission import normalise_tag
from isabelle.web_submission import parse_timestamp
from isabelle.web_submission import validate

TAGS = ["stardance", "ama", "workshop", "social"]


def body(**overrides):
    payload = {
        "title": "Code in the Dark",
        "description": "We build a site with the CSS preview turned off.",
        "start_time": "2026-10-01T17:00:00.000Z",
        "end_time": "2026-10-01T19:00:00.000Z",
        "leader_slack_id": "U0TESTLEADER",
        "tags": ["workshop"],
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def client():
    return TestClient(api)


class TestParseTimestamp:
    def test_accepts_utc_z_suffix(self):
        assert parse_timestamp("2026-10-01T17:00:00.000Z") == datetime(
            2026, 10, 1, 17, 0
        )

    def test_normalises_an_offset_to_naive_utc(self):
        assert parse_timestamp("2026-10-01T19:00:00+02:00") == datetime(
            2026, 10, 1, 17, 0
        )

    @pytest.mark.parametrize("value", ["", "   ", "not a date", None, 12345])
    def test_rejects_unparseable_values(self, value):
        assert parse_timestamp(value) is None


class TestAsRichText:
    def test_round_trips_through_rich_text_to_md(self):
        from isabelle.utils.utils import rich_text_to_md

        text = "Come hang out."
        assert rich_text_to_md(as_rich_text(text)).strip() == text


class TestValidate:
    def test_accepts_a_well_formed_submission(self):
        errors, values = validate(body(), TAGS)
        assert errors == {}
        assert values["title"] == "Code in the Dark"
        assert values["tags"] == ["workshop"]

    def test_requires_title_description_and_leader(self):
        errors, _ = validate(
            body(title="  ", description="", leader_slack_id=""), TAGS
        )
        assert "title" in errors
        assert "description" in errors
        assert "leader_slack_id" in errors

    def test_caps_title_length(self):
        errors, _ = validate(body(title="x" * (MAX_TITLE + 1)), TAGS)
        assert "title" in errors

    def test_rejects_end_before_or_equal_to_start(self):
        errors, _ = validate(body(end_time="2026-10-01T17:00:00.000Z"), TAGS)
        assert "end_time" in errors

    def test_rejects_events_longer_than_a_day(self):
        errors, _ = validate(body(end_time="2026-10-03T17:00:00.000Z"), TAGS)
        assert "end_time" in errors

    def test_defaults_the_event_link(self):
        _, values = validate(body(), TAGS)
        assert values["event_link"] == DEFAULT_EVENT_LINK

    @pytest.mark.parametrize(
        "url", ["javascript:alert(1)", "http://example.com", "ftp://example.com"]
    )
    def test_rejects_non_https_links(self, url):
        assert "event_link" in validate(body(event_link=url), TAGS)[0]
        assert "rsvp_form_url" in validate(body(rsvp_form_url=url), TAGS)[0]

    def test_keeps_tags_that_are_not_yet_known(self):
        _, values = validate(body(tags=["workshop", "movie-night"]), TAGS)
        assert values["tags"] == ["workshop", "movie-night"]

    def test_normalises_a_typed_name_into_a_slug(self):
        _, values = validate(body(tags=["  Movie Night!! "]), TAGS)
        assert values["tags"] == ["movie-night"]

    def test_drops_names_with_nothing_usable(self):
        _, values = validate(body(tags=["!!!", "   "]), TAGS)
        assert values["tags"] == []

    def test_removes_duplicates(self):
        _, values = validate(body(tags=["AMA", "ama", " ama "]), TAGS)
        assert values["tags"] == ["ama"]

    def test_caps_the_number_of_tags(self):
        _, values = validate(body(tags=list("abcdefgh")), TAGS)
        assert len(values["tags"]) == 6

    def test_ignores_tags_that_are_not_a_list(self):
        _, values = validate(body(tags="workshop"), TAGS)
        assert values["tags"] == []

    def test_never_returns_an_approved_flag(self):
        _, values = validate(body(approved=True), TAGS)
        assert "approved" not in values


class TestEndpointAuth:
    def test_rejects_a_missing_secret(self, client):
        assert client.post("/internal/events", json=body()).status_code == 401

    def test_rejects_a_wrong_secret(self, client):
        response = client.post(
            "/internal/events",
            json=body(),
            headers={"x-internal-secret": "not-the-secret"},
        )
        assert response.status_code == 401

    def test_rejects_a_malformed_body(self, client, rsvp_secret):
        response = client.post(
            "/internal/events",
            json=body(title=""),
            headers={"x-internal-secret": rsvp_secret},
        )
        assert response.status_code == 422
        assert "title" in response.json()["errors"]


class TestNormaliseTag:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("Movie Night", "movie-night"),
            ("  AMA  ", "ama"),
            ("a//b", "ab"),
            ("--messy--", "messy"),
            ("", ""),
            (None, ""),
            ("x" * 40, "x" * 24),
        ],
    )
    def test_slugs(self, raw, expected):
        assert normalise_tag(raw) == expected
