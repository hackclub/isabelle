# Isabelle

Isabelle is a Slack bot for discovering events in the Hack Club Slack. It provides an easy way for SAD members to add events to the Hack Club [events website](https://events.hackclub.com) and for Hack Clubbers to find events and show interest in events.

## Features

- Event Timeline
- Creating Events & event management
- Showing Interest in Events
- Alerts when an event starts via DMs and email


Visit the [App Home](slack://app?team=T0266FRGM&id=A07S8R2G3SQ) to see upcoming events and create or propose new events.

## Development

To run the bot locally, you'll need to set up a Slack app and will need access to the Airtable base. You'll need to set the following environment variables:

- `SLACK_SIGNING_SECRET` - _the signing secret for the Slack app. Found on the Slack app dashboard_
- `SLACK_BOT_TOKEN` - _the bot token for the Slack app. Found on the Slack app dashboard after authorising the app_
- `SLACK_SAD_CHANNEL` - _the ID of the private SAD channel. Get this from the channel URL_
- `SLACK_APPROVAL_CHANNEL`- _the ID of the channel events are sent to for approval. Get this from the channel URL_
- `AIRTABLE_API_KEY` - _the API key for the Airtable base. Get this from [here](https://airtable.com/create/tokens/new)_
- `AIRTABLE_BASE_ID` - _the ID of the Airtable base. Get this from the URL (begins with `app`)_
- `GOOGLE_USERNAME` - _the email address of the Google account to use for sending emails_
- `GOOGLE_PASSWORD` - _the app password of the Google account to use for sending emails_
- `PORT` - _optional, defaults to 3000_

For the Slack app, here is the manifest you will need. Make sure to change the command and request URLs.

```json
{
    "display_information": {
        "name": "Isabelle",
        "description": "Broadcasting events straight to you!",
        "background_color": "#1a8779"
    },
    "features": {
        "app_home": {
            "home_tab_enabled": true,
            "messages_tab_enabled": true,
            "messages_tab_read_only_enabled": true
        },
        "bot_user": {
            "display_name": "Isabelle",
            "always_online": false
        },
        "slash_commands": [
            {
                "command": "/create-event",
                "url": "REQUEST_URL",
                "description": "Create an event for events.hackclub.com",
                "should_escape": false
            }
        ]
    },
    "oauth_config": {
        "scopes": {
            "bot": [
                "channels:history",
                "chat:write",
                "chat:write.public",
                "commands",
                "groups:history",
                "groups:read",
                "users:read",
                "users:read.email"
            ]
        }
    },
    "settings": {
        "event_subscriptions": {
            "request_url": "REQUEST_URL",
            "bot_events": [
                "app_home_opened"
            ]
        },
        "interactivity": {
            "is_enabled": true,
            "request_url": "REQUEST_URL"
        },
        "org_deploy_enabled": false,
        "socket_mode_enabled": false,
        "token_rotation_enabled": false
    }
}
```

To actually run the bot, you can use the following commands:

```bash
git clone https://github.com/DillonB07/EventManager
cd EventManager
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```
