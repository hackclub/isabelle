from pyairtable import Api
from datetime import datetime, timezone


class AirtableManager:
    def __init__(self, api_key: str, base_id: str):
        api = Api(api_key)
        self.events_table = api.table(base_id, "Events")
        self.users_table = api.table(base_id, "Users")
        print("Connected to Airtable")

    def create_event(
        self,
        title: str,
        description: str,
        start_time: str,
        end_time: str,
        location: str,
        host_id: str,
        host_name: str,
        host_pfp: str,
    ):
        event = self.events_table.create(
            {
                "Title": title,
                "Description": description,
                "Start Time": datetime.fromtimestamp(
                    start_time, timezone.utc
                ).isoformat(),
                "End Time": datetime.fromtimestamp(end_time, timezone.utc).isoformat(),
                "Event Link": location,
                "Leader Slack ID": host_id,
                "Leader": host_name,
                "Avatar": [{"url": host_pfp}],
                "Approved": False,
            }
        )
        return event

    def update_event(self, id: str, **updates: dict):
        event = self.events_table.update(id, updates)
        return event

    def get_event(self, id: str):
        user = self.events_table.get(id)
        return user

    def get_all_events(self, unapproved: bool = False):
        events = self.events_table.all()
        if not unapproved:
            events = [
                event for event in events if event["fields"].get("Approved", False)
            ]
        events = sorted(events, key=lambda event: event["fields"]["Start Time"])
        return events

    def get_upcoming_events(self):
        events = self.events_table.all(view="Future Events")
        events = [event for event in events if event["fields"].get("Approved", False)]
        return events

    def update_event(
        self,
        id: str | None = None,
        **updates: dict,
    ):
        event = self.events_table.update(id, updates)
        return event

    def create_user(self, slack_id: str):
        user = self.users_table.create(
            {
                "Slack ID": slack_id,
            }
        )
        return user

    def get_user(self, slack_id: str):
        user = self.users_table.first(formula=f"{{Slack ID}} = '{slack_id}'")
        if not user:
            user = self.create_user(slack_id)
        return user

    def update_user(self, slack_id: str, **updates: dict):
        user = self.users_table.update(slack_id, updates)
        return user

    def get_rsvps_from_event(self, event_id: str):
        rsvps = self.users_table.all()
        rsvps = [
            rsvp
            for rsvp in rsvps
            if event_id in rsvp["fields"].get("Interesting Events", [])
        ]
        return rsvps

    def rsvp_to_event(self, event_id: str, slack_id: str):
        user = self.get_user(slack_id)
        events = user["fields"].get("Interesting Events", [])
        if event_id in events:
            events.remove(event_id)
        else:
            events.append(event_id)
        user = self.update_user(user["id"], **{"Interesting Events": events})
        return user
