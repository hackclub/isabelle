from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import uuid
import json
import logging
from urllib.parse import quote

from isabelle.tables import Event
from isabelle.utils.rich_text import to_rich_text_column

def get_cachet_pfp(user_id: str) -> str:
    return f"https://cachet.dunkirk.sh/users/{user_id}/r"


class DatabaseService:
    
    async def create_event(
        self,
        title: str,
        description: str,
        raw_description: List[Dict],
        start_time: datetime,
        end_time: datetime,
        leader_slack_id: str,
        leader_name: str,
        avatar_url: Optional[str] = None,
        event_link: Optional[str] = None,
        approved: bool = False,
        tags: Optional[List[str]] = None,
        rsvp_form_url: Optional[str] = None,
    ) -> Optional[Event]:
        
        raw_description_json = json.dumps({
            "type": "rich_text",
            "elements": raw_description,
        })
        
        event = Event(
            Title=title,
            Description=description,
            RawDescription=raw_description_json,
            StartTime=start_time,
            EndTime=end_time,
            LeaderSlackID=leader_slack_id,
            Leader=leader_name,
            Avatar=avatar_url or get_cachet_pfp(leader_slack_id),
            EventLink=event_link or "https://app.slack.com/huddle/T0266FRGM/C01D7AHKMPF",
            Approved=approved,
            RSVPData = {},
            Cancelled=False,
            InterestedUsers=[],
            InterestCount=0,
            Sent1DayReminder=False,
            Sent1HourReminder=False,
            SentStartingReminder=False,
            HasHappened=False,
            AMA=False,
            Tags=tags or [],
            RSVPFormURL=rsvp_form_url,
            Calculation=title.lower().replace(" ", "-").replace(":",""), # copied from the airtable formula
            CalendarLink=make_google_calendar_url(title=title,description=description,end=end_time,event_link=event_link,leader=leader_name,start=start_time)
        )

        try: 
            logging.info("Trying to insert event ", title)
            await Event.insert(event)
        except Exception as e:
            logging.error("Error creating event",e)
            return None
        logging.info("Event created successfully")
        
        return event
    
    async def get_event(self, event_id: str) -> Optional[Event]:
        try:
            event_uuid = uuid.UUID(event_id)
            return await Event.select().where(Event.id == event_uuid).output(load_json=True).first()
        except (ValueError, TypeError):
            return None
    
    async def get_all_events(self, include_unapproved: bool = False) -> List[Event]:
        query = Event.select().where(Event.Cancelled == False)
        
        if not include_unapproved:
            query = query.where(Event.Approved == True)
            
        return await query.order_by(Event.StartTime).output(load_json=True)
    
    async def get_upcoming_events(self, include_unapproved: bool = False) -> List[Event]:
        now = datetime.now()
        query = Event.select().where(
            Event.StartTime > now,
            Event.Cancelled == False
        )
        
        if not include_unapproved:
            query = query.where(Event.Approved == True)
            
        return await query.order_by(Event.StartTime).output(load_json=True)
    
    
    CALENDAR_FIELDS = {
        "Title",
        "Description",
        "Leader",
        "EventLink",
        "StartTime",
        "EndTime",
    }

    async def get_reminder_candidates(self) -> List[Event]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return await (
            Event.select()
            .where(
                Event.Approved == True,
                Event.Cancelled == False,
                Event.EndTime >= now,
            )
            .order_by(Event.StartTime)
            .output(load_json=True)
        )

    async def update_event(self, event_id: str, **updates) -> Optional[Event]:

        if self.CALENDAR_FIELDS & updates.keys():
            event = await self.get_event(event_id)
            if not event:
                return None

            start_time = updates.get("StartTime", event.get("StartTime"))
            end_time = updates.get("EndTime", event.get("EndTime"))
            updates["CalendarLink"] = make_google_calendar_url(
                title=updates.get("Title", event.get("Title")),
                description=updates.get("Description", event.get("Description")),
                leader=updates.get("Leader", event.get("Leader")),
                event_link=updates.get("EventLink", event.get("EventLink")),
                start=start_time,
                end=end_time
            )

            if "Title" in updates:
                title = updates["Title"] or ""
                updates["Calculation"] = title.lower().replace(" ", "-").replace(":", "")


        try:
            event_uuid = uuid.UUID(event_id) 
            await Event.update(**updates).where(Event.id == event_uuid)
            return await Event.select().where(Event.id == event_uuid).output(load_json=True).first()
        except (ValueError, TypeError) as e:
            logging.error(e)
            return None
    
    async def approve_event(self, event_id: str) -> Optional[Event]:
        return await self.update_event(event_id, Approved=True)
    
    async def cancel_event(
        self,
        event_id: str,
        reason=None,
        kind: str = "cancelled",
    ) -> Optional[Event]:
        updates = {
            "Cancelled": True,
            "Approved": False,
            "CancellationType": kind,
        }
        if reason:
            updates["RawCancellation"] = to_rich_text_column(reason)
        return await self.update_event(event_id, **updates)
    
    async def toggle_user_interest(self, event_id: str, user_slack_id: str, forced_state: Optional[bool] = None, user_info: Optional[Dict[str, Any]] = None) -> Optional[Event]:
        try:
            event_uuid = uuid.UUID(event_id)
            event = await Event.objects().where(Event.id == event_uuid).output(load_json=True).first()
            
            if not event:
                return None
            
            rsvp_data = dict(event.RSVPData or {})
            if isinstance(rsvp_data, str):
                try:
                    import json
                    rsvp_data = json.loads(rsvp_data)
                except Exception:
                    rsvp_data = {}
            legacy_users: list = list(event.InterestedUsers or [])

            sub = user_info.get("sub") if user_info else None
            rsvp_key = sub or user_slack_id

            in_rsvp_data = rsvp_key in rsvp_data
            in_legacy = user_slack_id in legacy_users
            currently_attending = in_rsvp_data or in_legacy

            if forced_state is True:
                should_attend = True
            elif forced_state is False:
                should_attend = False
            else:
                should_attend = not currently_attending

            if not should_attend and not currently_attending:
                return await Event.select().where(Event.id == event_uuid).output(load_json=True).first()

            if should_attend:
                rsvp_data[rsvp_key] = {
                    "sub" : sub,
                    "slackId": user_slack_id,
                    "name": user_info.get("name") if user_info else None,
                    "email": user_info.get("email") if user_info else None,
                    "slackDisplayName": user_info.get("slackDisplayName") if user_info else None,
                    "rsvpedAt": datetime.now(timezone.utc).isoformat(),
                }
            else:
                rsvp_data.pop(rsvp_key, None)
                if user_slack_id != rsvp_key:
                    rsvp_data.pop(user_slack_id, None)
                stale = [k for k, v in rsvp_data.items() if v.get("slackId") == user_slack_id]
                for k in stale:
                    rsvp_data.pop(k)

            rsvp_slack_ids = {v.get("slackId") for v in rsvp_data.values() if v.get("slackId")}
            legacy_only = [uid for uid in legacy_users if uid not in rsvp_slack_ids]
            new_count = len(rsvp_data) + len(legacy_only)

            await Event.update(
                RSVPData=rsvp_data,
                InterestCount=new_count,
                # InterestedUsers - will no longer be written (exists in the backend for already RSVPed users btw)!
            ).where(Event.id == event_uuid)
            return await Event.select().where(Event.id == event_uuid).output(load_json=True).first()
        except (ValueError, TypeError) as e:
            logging.error("toggle_user_interest error: %s", e)
            return None
    
    async def get_interested_users(self, event_id: str) -> List[str]:
        """legacy: returns union of slack IDs from both sources, we should remove InterestedUsers later tho"""
        event = await self.get_event(event_id)

        if not event:
            return []
        legacy = list(event.get("InterestedUsers") or [])
        rsvp_slack_ids = [
            v["slackId"]
            for v in (event.get("RSVPData") or {}).values()
            if v.get("slackId")
        ]
        combined = list(legacy)
        legacy_set = set(legacy)
        for sid in rsvp_slack_ids:
            if sid not in legacy_set:
                combined.append(sid)

        return combined
    
    async def set_rsvp_message(self, event_id: str, message_ts: str, channel_id: str, emoji: Optional[str] = None) -> bool:
        emoji_part = emoji or "any"
        rsvp_msg = f"{message_ts}/{channel_id}/{emoji_part}"
        
        result = await self.update_event(event_id, rsvpMsg=rsvp_msg)
        return result is not None
    
    async def get_event_by_rsvp(self, message_ts:str, channel_id:str, emoji: str) -> Optional[Event]:
        event = await Event.select().where(Event.rsvpMsg == f"{message_ts}/{channel_id}/{emoji}").output(load_json=True).first()

        return event or None

    async def set_rsvp_msg(self, event_id: str, message_ts: str, channel_id:str, emoji: Optional[str]) -> Optional[Event]:
        e = emoji or "any"
        if type(message_ts) is not str or type(channel_id) is not str:
            raise Exception("invalid message ts or channel id")
        return await self.update_event(event_id=event_id, **{"rsvpMsg":f"{message_ts}/{channel_id}/{e}"})


def make_google_calendar_url(title, description, leader, event_link, start, end):
    s = start.strftime("%Y%m%dT%H%M00Z")
    e = end.strftime("%Y%m%dT%H%M00Z")
    return (
        "https://www.google.com/calendar/render?action=TEMPLATE"
        f"&text={quote(title)}"
        f"&details={quote(f'{description}\\nHack Club Event by {leader}')}"
        f"&location={quote(event_link)}"
        f"&dates={s}%2F{e}"
    )
