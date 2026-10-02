import pytest

from isabelle.utils.env import Environment

DIGEST_VARS = (
    "EVENTS_DIGEST_CHANNEL",
    "EVENTS_DIGEST_FREQUENCY",
    "EVENTS_DIGEST_HOUR",
    "EVENTS_DIGEST_WEEKDAY",
    "EVENTS_DIGEST_MAX_EVENTS",
    "EVENTS_DIGEST_REPOST_AFTER_MESSAGES",
)


@pytest.fixture(autouse=True)
def clean_digest_env(monkeypatch):
    for name in DIGEST_VARS:
        monkeypatch.delenv(name, raising=False)


def test_defaults_load_with_the_digest_off():
    environment = Environment()
    assert environment.digest_channel is None
    assert environment.digest_frequency == "weekly"
    assert environment.digest_hour == 14


def test_bad_settings_are_ignored_while_the_digest_is_off(monkeypatch):
    monkeypatch.setenv("EVENTS_DIGEST_FREQUENCY", "fortnightly")
    monkeypatch.setenv("EVENTS_DIGEST_HOUR", "not a number")
    monkeypatch.setenv("EVENTS_DIGEST_MAX_EVENTS", "99")
    Environment()


def test_valid_settings_load_when_enabled(monkeypatch):
    monkeypatch.setenv("EVENTS_DIGEST_CHANNEL", "C0NEWS")
    monkeypatch.setenv("EVENTS_DIGEST_FREQUENCY", "Biweekly")
    monkeypatch.setenv("EVENTS_DIGEST_HOUR", "9")
    environment = Environment()
    assert environment.digest_channel == "C0NEWS"
    assert environment.digest_frequency == "biweekly"
    assert environment.digest_hour == 9


@pytest.mark.parametrize(
    "name,value",
    [
        ("EVENTS_DIGEST_FREQUENCY", "fortnightly"),
        ("EVENTS_DIGEST_FREQUENCY", "weekly   # daily | weekly"),
        ("EVENTS_DIGEST_HOUR", "24"),
        ("EVENTS_DIGEST_HOUR", "not a number"),
        ("EVENTS_DIGEST_WEEKDAY", "7"),
        ("EVENTS_DIGEST_MAX_EVENTS", "0"),
        ("EVENTS_DIGEST_MAX_EVENTS", "17"),
        ("EVENTS_DIGEST_REPOST_AFTER_MESSAGES", "201"),
        ("EVENTS_DIGEST_REPOST_AFTER_MESSAGES", "14   # messages"),
    ],
)
def test_bad_settings_fail_on_boot_when_enabled(monkeypatch, name, value):
    monkeypatch.setenv("EVENTS_DIGEST_CHANNEL", "C0NEWS")
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match=name):
        Environment()
