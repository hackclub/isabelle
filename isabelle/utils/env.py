import os

from dotenv import load_dotenv

from isabelle.utils.database import DatabaseService
# from .email import Email

load_dotenv()

DIGEST_FREQUENCIES = ("daily", "dailyish", "weekly", "biweekly")


def _int_env(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return None


def _within(value, low, high):
    return value is not None and low <= value <= high


class Environment:
    def __init__(self):
        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN", "unset")
        self.slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "unset")
        self.slack_approval_channel = os.environ.get("SLACK_APPROVAL_CHANNEL", "unset")
        self.slack_sad_channel = os.environ.get("SLACK_SAD_CHANNEL", "unset")
        self.airtable_api_key = os.environ.get("AIRTABLE_API_KEY", "unset")
        self.airtable_base_id = os.environ.get("AIRTABLE_BASE_ID", "unset")
        # google_username = os.environ.get("GOOGLE_USERNAME", "unset")
        # google_password = os.environ.get("GOOGLE_PASSWORD", "unset")
        self.sentry_dsn = os.environ.get("SENTRY_DSN", None)
        self.environemnt = os.environ.get("ENVIRONMENT", "development")
        self.testing = self.environemnt == "test"
        self.slack_app_token = os.environ.get("SLACK_APP_TOKEN")
        # for RSVPing
        self.events_rsvp_secret = os.environ.get("EVENTS_RSVP_SECRET", "unset")
        self.port = int(os.environ.get("PORT", 3000))

        # Scheduled event digest. Every one of these has a real default so that
        # adding the feature cannot break an existing deploy on boot — leaving
        # the channel unset is how you keep the digest switched off.
        self.digest_channel = os.environ.get("EVENTS_DIGEST_CHANNEL") or None
        self.digest_frequency = os.environ.get(
            "EVENTS_DIGEST_FREQUENCY", "weekly"
        ).strip().lower()
        self.digest_hour = _int_env("EVENTS_DIGEST_HOUR", 14)
        self.digest_weekday = _int_env("EVENTS_DIGEST_WEEKDAY", 0)
        self.digest_max_events = _int_env("EVENTS_DIGEST_MAX_EVENTS", 12)
        # "dailyish" only: how many channel messages since the last digest are
        # enough to justify reposting an unchanged line-up that has scrolled
        # out of view.
        self.digest_repost_after_messages = _int_env(
            "EVENTS_DIGEST_REPOST_AFTER_MESSAGES", 15
        )

        unset = [key for key, value in self.__dict__.items() if value == "unset"]

        if unset:
            raise ValueError(f"Missing environment variables: {', '.join(unset)}")

        # A misconfigured digest should fail on boot. The alternative is a
        # digest that silently never fires, which nobody notices for a week.
        # Only checked when a channel is set, so the digest settings cannot
        # take the rest of the service down while it is switched off.
        if self.digest_channel:
            if self.digest_frequency not in DIGEST_FREQUENCIES:
                raise ValueError(
                    "EVENTS_DIGEST_FREQUENCY must be one of "
                    f"{', '.join(DIGEST_FREQUENCIES)} (got '{self.digest_frequency}')"
                )

            if not _within(self.digest_hour, 0, 23):
                raise ValueError("EVENTS_DIGEST_HOUR must be 0-23")

            if not _within(self.digest_weekday, 0, 6):
                raise ValueError(
                    "EVENTS_DIGEST_WEEKDAY must be 0 (Monday) through 6 (Sunday)"
                )

            # Slack rejects a message over 50 blocks, and each event costs three
            # (divider, section, actions) on top of a header and a footer.
            if not _within(self.digest_max_events, 1, 16):
                raise ValueError("EVENTS_DIGEST_MAX_EVENTS must be 1-16")

            # conversations.history is asked for one page, so the threshold has to
            # fit inside a single reasonable page.
            if not _within(self.digest_repost_after_messages, 1, 200):
                raise ValueError("EVENTS_DIGEST_REPOST_AFTER_MESSAGES must be 1-200")

        if not self.sentry_dsn and self.environemnt == "production":
            raise Exception("SENTRY_DSN is not set")


        self.database = DatabaseService()

        # self.mailer = Email(sender=google_username, password=google_password)

        self.authorised_users = [
            "U054VC2KM9P",  # Amber
            "U0409FSKU82",  # Arpan
            "U01MPHKFZ7S",  # Aarya
            "UDK5M9Y13",    # Chris
            "U06QST7V0J2",  # Eesha
            "U097UCZE2BB",  # Aishaani
            "U072PTA5BNG",  # Victorio
            "U09Q8MLTE58"   # EPS
        ]

        self.event_tags = [
            "stardance",
            "ama",
            "workshop",
            "social",
        ]


env = Environment()
