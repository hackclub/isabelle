from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import JSONB

ID = "isabelle_rsvpdata_migration"
VERSION = "1.28.0"
DESCRIPTION = "adds the RSVPData column"

async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="isabelle", description=DESCRIPTION
    )
    manager.add_column(
        table_class_name="Event",
        tablename="event",
        column_name="RSVPData",
        db_column_name="RSVPData",
        column_class_name="JSONB",
        column_class=JSONB,
        params={
            "default": {},
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )
    return manager
