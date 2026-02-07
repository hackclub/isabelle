from pyairtable import Api
import asyncio
from datetime import datetime, timezone
#from isabelle.tables import Event
from isabelle.utils.env import env
#from isabelle.utils.database import get_cachet_pfp
import os
import requests
import json
api = Api(env.airtable_api_key)


table = api.table(env.airtable_base_id,'Events')

rows: list = table.all()

def upload_to_cdn(url: str) -> str:
    print(f"trying to upload  {url}")
    j = json.dumps({"url":url})
    res = requests.post("https://cdn.hackclub.com/api/v4/upload_from_url", data=j,headers={"Authorization":f"Bearer {os.getenv("CDN_API_KEY")}","Content-Type":"application/json"}).json()
    print(res)
    cdn_url = res.get("url")


    return cdn_url

def to_naive_utc(dt_str: str) -> datetime:
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

cdn_images = []

async def main():
    for row in rows:
        # e = Event(
        #         Title=row["fields"]["Title"],
        #         Description=row["fields"]["Description"],
        #         RawDescription=row["fields"].get("Raw Description", ""),
        #         StartTime= to_naive_utc(row["fields"]["Start Time"]),
        #         EndTime= to_naive_utc(row["fields"]["End Time"]),
        #         LeaderSlackID=row["fields"]["Leader Slack ID"],
        #         Leader=row["fields"]["Leader"],
        #         Avatar=get_cachet_pfp(row["fields"]["Leader Slack ID"]),
        #         EventLink=row["fields"].get("Event Link", "https://app.slack.com/huddle/T0266FRGM/C01D7AHKMPF"),
        #         Approved=row["fields"].get("Approved",False),
        #         Cancelled=row["fields"].get("Cancelled",False),
        #         InterestedUsers=[],
        #         InterestCount=0,
        #         Sent1DayReminder=row["fields"].get("Sent 1 Day Reminder",False),
        #         Sent1HourReminder=row["fields"].get("Sent 1 Hour Reminder",False),
        #         SentStartingReminder=row["fields"].get("Sent Starting Reminder",False),
        #         HasHappened=row["fields"].get("Has Happened",False) == "✅",
        #         AMA=row["fields"].get("AMA",False),
        #         Calculation=row["fields"]["Calculation"],
        #         CalendarLink=row["fields"]["Calendar Link"]
        #     )
        is_ama = row["fields"].get("AMA", False)

        avatar = row["fields"].get("AMA Avatar")
        ama_title = row["fields"].get("Title")
        if not is_ama or not avatar or not ama_title:
            print(is_ama,avatar,ama_title)
            continue

        image_link = avatar[0].get("url")

        cdn_url = upload_to_cdn(image_link)

        touple = (ama_title, cdn_url)
        print(touple)
        cdn_images.append(touple)        
        try:
#            await Event.insert(e)
            ...
        except Exception as ex:
 #           print(f"Error inserting event {e.Title}: {ex}")
            os._exit(1)
        finally:
            continue
    
    jai = json.dumps(cdn_images)
    with open("./ignore/dump.txt",'w') as f:
        f.write(jai)


if __name__ == '__main__':
    asyncio.run(main())