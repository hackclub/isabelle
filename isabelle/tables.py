from piccolo.table import Table
from piccolo.columns import Varchar,Boolean,Timestamp, SmallInt, Text, Array, UUID


# Schema copied form airtable using PascalCase
class Event(Table):
    id = UUID(primary_key=True)
    Title = Varchar()
    Description = Varchar()
    StartTime = Timestamp()
    EndTime = Timestamp()
    LeaderSlackID = Varchar(length=32)
    Leader = Varchar() # (Name)
    Avatar = Varchar() # URL
    Approved = Boolean()
    EventLink = Varchar() # URL
    Cancelled = Boolean()
    YouTubeURL = Varchar()
    Emoji = Varchar(length=32)
    HasHappened = Boolean()
    AMA = Boolean()
    AMAName = Varchar()
    AMACompany = Varchar()
    AMATitle = Varchar()
    AMALink = Varchar()
    AMAAvatar = Varchar() # URL
    CalendarLink = Varchar()
    Photos = Varchar() # URL
    # TODO Will not implement these rn. Not being used
    # Photos
    # Attendance = SmallInt()
    # AMAId = Varchar()
    Calculation = Varchar() # Readable ID
    Month = SmallInt()
    Sent1DayReminder = Boolean()
    Sent1HourReminder = Boolean()
    SentStartingReminder = Boolean()
    RawDescription = Text()
    RawCancellation = Text()
    # I'm not ready for DB relations and I think a ID's list will work
    # TODO: implement notify by email
    InterestedUsers = Array(base_column=Varchar())
    InterestCount = SmallInt() # I know this could easily be calculated but I will try to keep this as close to the airtable as possible
    rsvpMsg = Varchar()