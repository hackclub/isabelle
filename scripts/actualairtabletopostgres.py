from pyairtable import Api
import asyncio
from datetime import datetime, timezone
from isabelle.tables import Event
from isabelle.utils.env import env
from isabelle.utils.database import get_cachet_pfp
import os
api = Api(env.airtable_api_key)


table = api.table(env.airtable_base_id,'Events')

rows: list = table.all()

def to_naive_utc(dt_str: str) -> datetime:
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

async def main():
    print(rows)
    for row in rows:
        e = Event(
                Title=row["fields"]["Title"],
                Description=row["fields"]["Description"],
                RawDescription=row["fields"].get("Raw Description", ""),
                StartTime= to_naive_utc(row["fields"]["Start Time"]),
                EndTime= to_naive_utc(row["fields"]["End Time"]),
                LeaderSlackID=row["fields"]["Leader Slack ID"],
                Leader=row["fields"]["Leader"],
                Avatar=get_cachet_pfp(row["fields"]["Leader Slack ID"]),
                EventLink=row["fields"].get("Event Link", "https://app.slack.com/huddle/T0266FRGM/C01D7AHKMPF"),
                Approved=row["fields"].get("Approved",False),
                Cancelled=row["fields"].get("Cancelled",False),
                InterestedUsers=[],
                InterestCount=0,
                Sent1DayReminder=row["fields"].get("Sent 1 Day Reminder",False),
                Sent1HourReminder=row["fields"].get("Sent 1 Hour Reminder",False),
                SentStartingReminder=row["fields"].get("Sent Starting Reminder",False),
                HasHappened=row["fields"].get("Has Happened",False) == "✅",
                AMA=row["fields"].get("AMA",False),
                Calculation=row["fields"]["Calculation"],
                CalendarLink=row["fields"]["Calendar Link"]
            )

        try:
            await Event.insert(e)
            print(f"Inserted event {e.Title} successfully.")
        except Exception as ex:
            print(f"Error inserting event {e.Title}: {ex}")
            os._exit(1)
        finally:
            pass

if __name__ == '__main__':
    asyncio.run(main())