from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Varchar, Text, Timestamp, UUID
from piccolo.columns.indexes import IndexMethod


ID = "2026-09-12T21:00:00:000000"
VERSION = "1.28.0"
DESCRIPTION = "People outside Hack Club who may submit events"


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="isabelle", description=DESCRIPTION
    )

    manager.add_table(
        class_name="Submitter", tablename="submitter", schema=None, columns=None
    )

    manager.add_column(
        table_class_name="Submitter",
        tablename="submitter",
        column_name="SlackID",
        db_column_name="SlackID",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 32,
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

    for name in ("Name", "Note"):
        manager.add_column(
            table_class_name="Submitter",
            tablename="submitter",
            column_name=name,
            db_column_name=name,
            column_class_name="Text",
            column_class=Text,
            params={
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

    manager.add_column(
        table_class_name="Submitter",
        tablename="submitter",
        column_name="AddedBySlackID",
        db_column_name="AddedBySlackID",
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

    manager.add_column(
        table_class_name="Submitter",
        tablename="submitter",
        column_name="AddedAt",
        db_column_name="AddedAt",
        column_class_name="Timestamp",
        column_class=Timestamp,
        params={
            "default": None,
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
