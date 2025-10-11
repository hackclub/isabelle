from contextlib import asynccontextmanager

from piccolo.engine import engine_finder
from piccolo_admin.endpoints import create_admin
from piccolo_api.crud.endpoints import PiccoloCRUD
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.requests import Request

from isabelle.endpoints import HomeEndpoint
from isabelle.piccolo_app import APP_CONFIG
from isabelle.tables import Event
from slack_bolt.adapter.starlette.async_handler import AsyncSlackRequestHandler
from isabelle.utils.slack import app 


async def open_database_connection_pool():
    try:
        engine = engine_finder()
        await engine.start_connection_pool()
    except Exception:
        print("Unable to connect to the database")


async def close_database_connection_pool():
    try:
        engine = engine_finder()
        await engine.close_connection_pool()
    except Exception:
        print("Unable to connect to the database")


@asynccontextmanager
async def lifespan(app: Starlette):
    await open_database_connection_pool()
    yield
    await close_database_connection_pool()


app_handler = AsyncSlackRequestHandler(app)


async def endpoint(req: Request):
    return await app_handler.handle(req)

api = Starlette(
    routes=[
        Route("/", HomeEndpoint),
        Mount(
            "/admin/",
            create_admin(
                tables=APP_CONFIG.table_classes,
                # allowed_hosts=['isabelle.hackclub.com']
            ),
        ),
        Mount("/static/", StaticFiles(directory="static")),
        Mount("/events/", PiccoloCRUD(table=Event)),
        Route("/slack/events",endpoint=endpoint, methods=["POST"])
    ],
    lifespan=lifespan,
)
