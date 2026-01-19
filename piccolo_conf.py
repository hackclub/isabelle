from piccolo.engine.postgres import PostgresEngine

from piccolo.conf.apps import AppRegistry
import os

DB = PostgresEngine(
    config={
        "database": "isatest",
        "user": "postgres",
        "password": os.getenv("POSTGRES_PASSWORD","postgres"),
        "host": os.getenv("POSTGRES_HOST","localhost"),
        "port": int(os.getenv("POSTGRES_PORT","5432")),
    }
)

APP_REGISTRY = AppRegistry(
    apps=["isabelle.piccolo_app", "piccolo_admin.piccolo_app"]
)
