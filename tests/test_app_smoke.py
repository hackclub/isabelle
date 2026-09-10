from starlette.testclient import TestClient

from app import api


def test_app_imports_without_live_slack_credentials():
    assert api is not None


def test_expected_routes_are_registered():
    paths = {getattr(route, "path", None) for route in api.routes}
    assert "/health" in paths
    assert "/internal/events/{event_id}/rsvp" in paths
    assert "/internal/events/{event_id}/rsvps" in paths


def test_events_crud_is_mounted():
    mounts = {getattr(route, "path", None) for route in api.routes}
    assert "/events" in mounts or "/events/" in mounts


def test_home_endpoint_responds():
    response = TestClient(api).get("/")
    assert response.status_code == 200
    assert "Isabelle" in response.text
