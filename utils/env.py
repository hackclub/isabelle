from .airtable import AirtableManager
from dotenv import load_dotenv
import os
from .email import Email

load_dotenv()


class Environment:
    def __init__(self):
        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
        self.slack_approval_channel = os.environ.get("SLACK_APPROVAL_CHANNEL")
        self.slack_sad_channel = os.environ.get("SLACK_SAD_CHANNEL")
        self.airtable_api_key = os.environ.get("AIRTABLE_API_KEY")
        self.airtable_base_id = os.environ.get("AIRTABLE_BASE_ID")
        google_username = os.environ.get("GOOGLE_USERNAME")
        google_password = os.environ.get("GOOGLE_PASSWORD")

        self.port = int(os.environ.get("PORT", 3000))

        if not self.slack_bot_token:
            raise Exception("SLACK_BOT_TOKEN is not set")
        if not self.slack_signing_secret:
            raise Exception("SLACK_SIGNING_SECRET is not set")
        if not self.slack_approval_channel:
            raise Exception("SLACK_APPROVAL_CHANNEL is not set")
        if not self.slack_sad_channel:
            raise Exception("SLACK_SAD_CHANNEL is not set")
        if not self.airtable_api_key:
            raise Exception("AIRTABLE_API_KEY is not set")
        if not self.airtable_base_id:
            raise Exception("AIRTABLE_BASE_ID is not set")
        if not google_username:
            raise Exception("GOOGLE_USERNAME is not set")
        if not google_password:
            raise Exception("GOOGLE_PASSWORD is not set")

        self.airtable = AirtableManager(
            api_key=self.airtable_api_key, base_id=self.airtable_base_id
        )

        self.mailer = Email(sender=google_username, password=google_password)

        self.authorised_users = [
            "U054VC2KM9P",  # Amber
            "U0409FSKU82",  # Arpan
            "U01MPHKFZ7S",  # Aarya
            "UDK5M9Y13",  # Chris
            "U06QST7V0J2",  # Eesha
        ]


env = Environment()
