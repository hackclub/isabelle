import asyncio
from isabelle.tables import Event
from isabelle.utils.env import env

async def main():
    rows = await Event.select().columns(Event.id, Event.AMAAvatar)
    for row in rows:
        aa:str = row.get("AMAAvatar")
        eid = row.get("id")
        if aa is None or aa == "":
            continue

        if not aa.startswith("https://hc-cdn.hel1.your-objectstorage.com"):
            continue
        print(row)
        new_url = f"https://cdn.hackclub.com/rescue?url={aa}"
        print(new_url)
        try:
            await Event.update({Event.AMAAvatar: new_url}).where(Event.id == eid)
            print(f"Inserted event {eid} successfully.")
        except Exception as ex:
            print(f"Error inserting event {eid}: {ex}")
        finally:
            pass

if __name__ == '__main__':
    asyncio.run(main())