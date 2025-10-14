from datetime import datetime, timezone
from typing import List, Optional, Dict
import uuid
import json

from isabelle.tables import Event


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
        avatar_url: str,
        event_link: Optional[str] = None,
        approved: bool = False
    ) -> Event:
        
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
            Avatar=avatar_url,
            EventLink=event_link or "https://app.slack.com/huddle/T0266FRGM/C01D7AHKMPF",
            Approved=approved,
            Cancelled=False,
            InterestedUsers=[],
            InterestCount=0,
            Sent1DayReminder=False,
            Sent1HourReminder=False,
            SentStartingReminder=False,
            HasHappened=False,
            AMA=False
        )
        
        await event.save()
        return event
    
    async def get_event(self, event_id: str) -> Optional[Event]:
        try:
            event_uuid = uuid.UUID(event_id)
            return await Event.objects().where(Event.id == event_uuid).first()
        except (ValueError, TypeError):
            return None
    
    async def get_all_events(self, include_unapproved: bool = False) -> List[Event]:
        query = Event.select().where(Event.Cancelled == False)
        
        if not include_unapproved:
            query = query.where(Event.Approved == True)
            
        return await query.order_by(Event.StartTime)
    
    async def get_upcoming_events(self, include_unapproved: bool = False) -> List[Event]:
        now = datetime.now(timezone.utc)
        query = Event.select().where(
            Event.StartTime > now,
            Event.Cancelled == False
        )
        
        if not include_unapproved:
            query = query.where(Event.Approved == True)
            
        return await query.order_by(Event.StartTime)
    
    
    async def update_event(self, event_id: str, **updates) -> Optional[Event]:
        try:
            event_uuid = uuid.UUID(event_id) 
            await Event.update(**updates).where(Event.id == event_uuid)
            return await Event.objects().where(Event.id == event_uuid).first()
        except (ValueError, TypeError):
            return None
    
    async def approve_event(self, event_id: str) -> Optional[Event]:
        return await self.update_event(event_id, Approved=True)
    
    async def cancel_event(self, event_id: str, reason: Optional[str] = None) -> Optional[Event]:
        updates = {"Cancelled": True}
        if reason:
            updates["RawCancellation"] = reason
        return await self.update_event(event_id, **updates)
    
    async def toggle_user_interest(self, event_id: str, user_slack_id: str) -> Optional[Event]:
        try:
            event_uuid = uuid.UUID(event_id)
            event = await Event.objects().where(Event.id == event_uuid).first()
            
            if not event:
                return None
                
            interested_users = list(event.InterestedUsers or [])
            
            if user_slack_id in interested_users:
                interested_users.remove(user_slack_id)
            else:
                interested_users.append(user_slack_id)
            
            await Event.update(
                InterestedUsers=interested_users,
                InterestCount=len(interested_users)
            ).where(Event.id == event_uuid)
            
            return await Event.objects().where(Event.id == event_uuid).first()
        except (ValueError, TypeError):
            return None
    
    async def get_interested_users(self, event_id: str) -> List[str]:
        event = await self.get_event(event_id)

        if not event:
            return []
        return list(event.InterestedUsers or [])
    
    async def set_rsvp_message(self, event_id: str, message_ts: str, channel_id: str, emoji: Optional[str] = None) -> bool:
        emoji_part = emoji or "any"
        rsvp_msg = f"{message_ts}/{channel_id}/{emoji_part}"
        
        result = await self.update_event(event_id, rsvpMsg=rsvp_msg)
        return result is not None
    
    async def get_event_by_rsvp(self, message_ts:str, channel_id:str, emoji: str) -> Optional[Event]:
        event = await Event.select().where(Event.rsvpMsg == f"{message_ts}/{channel_id}/{emoji}").first()

        return event or None

