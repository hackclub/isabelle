from piccolo.apps.migrations.auto.migration_manager import MigrationManager


ID = "2025-10-11T02:27:01:886523"
VERSION = "1.28.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="", description=DESCRIPTION
    )

    def run():
        print(f"running {ID}")

    manager.add_raw(run)

    return manager
