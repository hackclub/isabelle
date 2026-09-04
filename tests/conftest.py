import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test")
os.environ.setdefault("SLACK_SIGNING_SECRET", "test-signing-secret")
os.environ.setdefault("SLACK_APPROVAL_CHANNEL", "C0TESTAPPROVAL")
os.environ.setdefault("SLACK_SAD_CHANNEL", "C0TESTSAD")
os.environ.setdefault("AIRTABLE_API_KEY", "unused")
os.environ.setdefault("AIRTABLE_BASE_ID", "unused")
os.environ.setdefault("EVENTS_RSVP_SECRET", "test-rsvp-secret")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from isabelle.tables import Event  # noqa: E402


@pytest.fixture(scope="session")
def rsvp_secret() -> str:
    return os.environ["EVENTS_RSVP_SECRET"]


@pytest_asyncio.fixture
async def clean_events():
    await Event.delete(force=True)
    yield
    await Event.delete(force=True)
