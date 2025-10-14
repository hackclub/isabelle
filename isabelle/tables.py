from piccolo.table import Table
from piccolo.columns import Varchar,Boolean,Timestamp, SmallInt, Text, Array, UUID


# Schema copied form airtable using PascalCase
class Event(Table):
    id = UUID(primary_key=True)
    Title = Text()
    Description = Text(null=True)
    StartTime = Timestamp(null=True)
    EndTime = Timestamp(null=True)
    LeaderSlackID = Varchar(length=32,null=True)
    Leader = Text(null=True) # (Name)
    Avatar = Text(null=True) # URL
    Approved = Boolean()
    EventLink = Varchar(null=True) # URL
    Cancelled = Boolean()
    YouTubeURL = Text(null=True)
    Emoji = Varchar(length=32,null=True)
    HasHappened = Boolean()
    AMA = Boolean()
    AMAName = Text(null=True)
    AMACompany = Text(null=True)
    AMATitle = Text(null=True)
    AMALink = Text(null=True)
    AMAAvatar = Text(null=True) # URL
    CalendarLink = Text(null=True)
    Photos = Text(null=True) # URL
    # TODO Will not implement these rn. Not being used
    # Photos
    # Attendance = SmallInt()
    # AMAId = Varchar()
    Calculation = Varchar(null=True) # Readable ID
    Month = SmallInt(null=True)
    Sent1DayReminder = Boolean()
    Sent1HourReminder = Boolean()
    SentStartingReminder = Boolean()
    RawDescription = Text(null=True)
    RawCancellation = Text(null=True)
    # I'm not ready for DB relations and I think a ID's list will work
    # TODO: implement notify by email
    InterestedUsers = Array(base_column=Text(),default=[])
    InterestCount = SmallInt() # I know this could easily be calculated but I will try to keep this as close to the airtable as possible
    rsvpMsg = Text(null=True)