from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Timestamptz
from piccolo.columns.column_types import UUID
from piccolo.columns.column_types import Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.indexes import IndexMethod


ID = "2026-09-16T14:00:41:120115"
VERSION = "1.28.0"
DESCRIPTION = "Add DigestState for the scheduled event digest"


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="isabelle", description=DESCRIPTION
    )

    manager.add_table(
        class_name="DigestState",
        tablename="digest_state",
        schema=None,
        columns=None,
    )

    manager.add_column(
        table_class_name="DigestState",
        tablename="digest_state",
        column_name="id",
        db_column_name="id",
        column_class_name="UUID",
        column_class=UUID,
        params={
            "default": UUID4(),
            "null": False,
            "primary_key": True,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    manager.add_column(
        table_class_name="DigestState",
        tablename="digest_state",
        column_name="Key",
        db_column_name="Key",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 64,
            "default": "",
            "null": False,
            "primary_key": False,
            "unique": True,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    manager.add_column(
        table_class_name="DigestState",
        tablename="digest_state",
        column_name="LastPostedAt",
        db_column_name="LastPostedAt",
        column_class_name="Timestamptz",
        column_class=Timestamptz,
        params={
            "default": TimestamptzNow(),
            "null": True,
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
