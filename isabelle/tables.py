from piccolo.table import Table
from piccolo.columns import Varchar,Boolean,Timestamp, Timestamptz, SmallInt, Text, Array, UUID, JSONB


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
    RSVPFormURL = Text(null=True)
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
    InterestedUsers = Array(base_column=Text(),default=[], secret=True)
    RSVPData = JSONB(default={}, secret=True)
    InterestCount = SmallInt() # I know this could easily be calculated but I will try to keep this as close to the airtable as possible
    rsvpMsg = Text(null=True)
    Tags = Array(base_column=Text(), default=[])


# Bookkeeping for the scheduled event digest. The digest runs from a worker
# loop rather than a cron, so "have we already posted this period" has to
# survive a restart — otherwise every redeploy posts again.
class DigestState(Table):
    id = UUID(primary_key=True)
    Key = Varchar(length=64, unique=True)
    # When a digest last actually went out. The "dailyish" frequency measures
    # channel activity from this point, so a suppressed slot must not move it.
    LastPostedAt = Timestamptz(null=True, default=None)
    # When a scheduled slot was last evaluated, whether or not it posted. This
    # is what stops one slot being reconsidered every 60 seconds.
    LastCheckedAt = Timestamptz(null=True, default=None)
    # Slack ts of the last digest, used as the "count messages after this"
    # cursor for conversations.history.
    LastMessageTs = Varchar(length=32, null=True)
    # The event ids the last digest listed, so "dailyish" can tell a genuinely
    # new line-up from the same one over again.
    LastEventIds = Array(base_column=Text(), default=[])
