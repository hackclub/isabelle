import uuid

import pytest
from starlette.testclient import TestClient

from app import api
from isabelle.utils.env import env

REVIEWER = env.authorised_users[0]
STRANGER = "U0STRANGER"
EVENT_ID = str(uuid.uuid4())

MUTATIONS = [
    ("post", f"/internal/events/{EVENT_ID}/approve"),
    ("post", f"/internal/events/{EVENT_ID}/cancel"),
    ("patch", f"/internal/events/{EVENT_ID}"),
]

READS = [
    "/internal/permissions",
    "/internal/events/manage",
    f"/internal/events/{EVENT_ID}/manage",
]


@pytest.fixture
def client():
    return TestClient(api)


def call(client, method, path, **kwargs):
    return getattr(client, method)(path, **kwargs)


class TestSecretIsRequired:
    @pytest.mark.parametrize("method, path", MUTATIONS)
    def test_mutations_reject_a_missing_secret(self, client, method, path):
        assert call(client, method, path, json={}).status_code == 401

    @pytest.mark.parametrize("method, path", MUTATIONS)
    def test_mutations_reject_a_wrong_secret(self, client, method, path):
        response = call(
            client, method, path, json={}, headers={"x-internal-secret": "nope"}
        )
        assert response.status_code == 401

    @pytest.mark.parametrize("path", READS)
    def test_reads_reject_a_missing_secret(self, client, path):
        assert client.get(path).status_code == 401


class TestActorIsRequired:
    @pytest.mark.parametrize("method, path", MUTATIONS)
    def test_a_valid_secret_alone_is_not_an_actor(self, client, method, path, rsvp_secret):
        response = call(
            client, method, path, json={}, headers={"x-internal-secret": rsvp_secret}
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("path", READS)
    def test_reads_require_an_actor(self, client, path, rsvp_secret):
        response = client.get(path, headers={"x-internal-secret": rsvp_secret})
        assert response.status_code == 422


class TestReviewerOnlyActions:
    def test_approve_rejects_a_non_reviewer(self, client, rsvp_secret):
        response = client.post(
            f"/internal/events/{EVENT_ID}/approve",
            json={"actor_slack_id": STRANGER},
            headers={"x-internal-secret": rsvp_secret},
        )
        assert response.status_code == 403

    def test_cancel_rejects_a_non_reviewer(self, client, rsvp_secret):
        response = client.post(
            f"/internal/events/{EVENT_ID}/cancel",
            json={"actor_slack_id": STRANGER, "reason": "because"},
            headers={"x-internal-secret": rsvp_secret},
        )
        assert response.status_code == 403

    def test_pending_scope_rejects_a_non_reviewer(self, client, rsvp_secret):
        response = client.get(
            "/internal/events/manage",
            params={"actor_slack_id": STRANGER, "scope": "pending"},
            headers={"x-internal-secret": rsvp_secret},
        )
        assert response.status_code == 403


class TestCancelValidation:
    def test_reason_is_required(self, client, rsvp_secret):
        response = client.post(
            f"/internal/events/{EVENT_ID}/cancel",
            json={"actor_slack_id": REVIEWER},
            headers={"x-internal-secret": rsvp_secret},
        )
        assert response.status_code == 422
        assert "reason" in response.json()["errors"]

    def test_a_blank_reason_is_not_a_reason(self, client, rsvp_secret):
        response = client.post(
            f"/internal/events/{EVENT_ID}/cancel",
            json={"actor_slack_id": REVIEWER, "reason": "    "},
            headers={"x-internal-secret": rsvp_secret},
        )
        assert response.status_code == 422


class TestScopeValidation:
    def test_unknown_scope_is_rejected(self, client, rsvp_secret):
        response = client.get(
            "/internal/events/manage",
            params={"actor_slack_id": REVIEWER, "scope": "everything"},
            headers={"x-internal-secret": rsvp_secret},
        )
        assert response.status_code == 422


class TestPermissions:
    @pytest.mark.db
    def test_reports_reviewer_status(self, client, rsvp_secret):
        for actor, expected in ((REVIEWER, True), (STRANGER, False)):
            response = client.get(
                "/internal/permissions",
                params={"actor_slack_id": actor},
                headers={"x-internal-secret": rsvp_secret},
            )
            assert response.status_code == 200
            assert response.json()["reviewer"] is expected
