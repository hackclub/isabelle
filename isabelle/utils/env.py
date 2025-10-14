import os

from dotenv import load_dotenv

from isabelle.utils.airtable import AirtableManager
from isabelle.utils.database import DatabaseService
# from .email import Email

load_dotenv()


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
        self.slack_app_token = os.environ.get("SLACK_APP_TOKEN")

        self.port = int(os.environ.get("PORT", 3000))

        unset = [key for key, value in self.__dict__.items() if value == "unset"]

        if unset:
            raise ValueError(f"Missing environment variables: {', '.join(unset)}")

        if not self.sentry_dsn and self.environemnt == "production":
            raise Exception("SENTRY_DSN is not set")

        self.airtable = AirtableManager(
            api_key=self.airtable_api_key,
            base_id=self.airtable_base_id,
            production=self.environemnt == "production",
        )

        self.database = DatabaseService()

        # self.mailer = Email(sender=google_username, password=google_password)

        self.authorised_users = [
            "U054VC2KM9P",  # Amber
            "U0409FSKU82",  # Arpan
            "U01MPHKFZ7S",  # Aarya
            "UDK5M9Y13",  # Chris
            "U06QST7V0J2",  # Eesha
            "U072PTA5BNG"   # Victorio
        ]


env = Environment()
