from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Array
from piccolo.columns.column_types import SmallInt
from piccolo.columns.column_types import Text
from piccolo.columns.column_types import Timestamp
from piccolo.columns.column_types import Varchar


ID = "2025-10-11T12:26:34:653546"
VERSION = "1.28.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="isabelle", description=DESCRIPTION
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="Description",
        db_column_name="Description",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="StartTime",
        db_column_name="StartTime",
        params={"null": True},
        old_params={"null": False},
        column_class=Timestamp,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="EndTime",
        db_column_name="EndTime",
        params={"null": True},
        old_params={"null": False},
        column_class=Timestamp,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="Leader",
        db_column_name="Leader",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="Avatar",
        db_column_name="Avatar",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="EventLink",
        db_column_name="EventLink",
        params={"null": True},
        old_params={"null": False},
        column_class=Varchar,
        old_column_class=Varchar,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="YouTubeURL",
        db_column_name="YouTubeURL",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="AMAName",
        db_column_name="AMAName",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="AMACompany",
        db_column_name="AMACompany",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="AMATitle",
        db_column_name="AMATitle",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="AMALink",
        db_column_name="AMALink",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="AMAAvatar",
        db_column_name="AMAAvatar",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="CalendarLink",
        db_column_name="CalendarLink",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="Photos",
        db_column_name="Photos",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="Calculation",
        db_column_name="Calculation",
        params={"null": True},
        old_params={"null": False},
        column_class=Varchar,
        old_column_class=Varchar,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="Month",
        db_column_name="Month",
        params={"null": True},
        old_params={"null": False},
        column_class=SmallInt,
        old_column_class=SmallInt,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="RawDescription",
        db_column_name="RawDescription",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="RawCancellation",
        db_column_name="RawCancellation",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="InterestedUsers",
        db_column_name="InterestedUsers",
        params={"default": []},
        old_params={"default": list},
        column_class=Array,
        old_column_class=Array,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Event",
        tablename="event",
        column_name="rsvpMsg",
        db_column_name="rsvpMsg",
        params={"null": True},
        old_params={"null": False},
        column_class=Text,
        old_column_class=Text,
        schema=None,
    )

    return manager
