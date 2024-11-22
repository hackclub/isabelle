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
