import json
from isabelle.tables import Event
import asyncio

file = open("./ignore/dump.txt","r")
content = file.read()

rows = json.loads(content)

async def main():
    for row in rows:
        print(row[1],row[0])
        await Event.update({
            Event.AMAAvatar: row[1]
        }).where(
            Event.Title == row[0]
        )


if __name__ == '__main__':
    asyncio.run(main())