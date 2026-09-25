from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Array
from piccolo.columns.column_types import Text
from piccolo.columns.column_types import Timestamptz
from piccolo.columns.column_types import Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.indexes import IndexMethod


ID = "2026-09-24T22:26:01:420842"
VERSION = "1.28.0"
DESCRIPTION = "Track dailyish digest state on DigestState"


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="isabelle", description=DESCRIPTION
    )

    manager.add_column(
        table_class_name="DigestState",
        tablename="digest_state",
        column_name="LastCheckedAt",
        db_column_name="LastCheckedAt",
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

    manager.add_column(
        table_class_name="DigestState",
        tablename="digest_state",
        column_name="LastEventIds",
        db_column_name="LastEventIds",
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

    manager.add_column(
        table_class_name="DigestState",
        tablename="digest_state",
        column_name="LastMessageTs",
        db_column_name="LastMessageTs",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 32,
            "default": "",
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
