from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Array
from piccolo.columns.column_types import Text
from piccolo.columns.indexes import IndexMethod


ID = "2026-05-30T11:17:04:123351"
VERSION = "1.28.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="isabelle", description=DESCRIPTION
    )

    manager.add_column(
        table_class_name="Event",
        tablename="event",
        column_name="Tags",
        db_column_name="Tags",
        column_class_name="Array",
        column_class=Array,
        params={
            "default": [],
            "base_column": Text(
                default="",
                null=False,
                primary_key=False,
                unique=False,
                index=False,
                index_method=IndexMethod.btree,
                choices=None,
                db_column_name=None,
                secret=False,
            ),
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    return manager
