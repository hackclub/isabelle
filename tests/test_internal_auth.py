import uuid

import pytest
from starlette.testclient import TestClient

from app import api

EVENT_ID = str(uuid.uuid4())


@pytest.fixture
def client():
    return TestClient(api)


def test_rsvp_rejects_missing_secret(client):
    response = client.put(
        f"/internal/events/{EVENT_ID}/rsvp",
        json={"slack_id": "U123", "attending": True},
    )
    assert response.status_code == 401


def test_rsvp_rejects_wrong_secret(client):
    response = client.put(
        f"/internal/events/{EVENT_ID}/rsvp",
        json={"slack_id": "U123", "attending": True},
        headers={"x-internal-secret": "not-the-secret"},
    )
    assert response.status_code == 401


def test_rsvp_list_rejects_missing_secret(client):
    response = client.get(f"/internal/events/{EVENT_ID}/rsvps")
    assert response.status_code == 401


def test_rsvp_list_rejects_wrong_secret(client):
    response = client.get(
        f"/internal/events/{EVENT_ID}/rsvps",
        headers={"x-internal-secret": "not-the-secret"},
    )
    assert response.status_code == 401


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"slack_id": "U123"},
        {"attending": True},
        {"slack_id": "U123", "attending": "yes"},
        {"slack_id": "", "attending": True},
    ],
)
def test_rsvp_rejects_malformed_body(client, rsvp_secret, body):
    response = client.put(
        f"/internal/events/{EVENT_ID}/rsvp",
        json=body,
        headers={"x-internal-secret": rsvp_secret},
    )
    assert response.status_code == 422
