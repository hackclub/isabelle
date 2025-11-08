from contextlib import asynccontextmanager

from piccolo.engine import engine_finder
from piccolo_admin.endpoints import create_admin
from piccolo_api.crud.endpoints import PiccoloCRUD
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import JSONResponse

from isabelle.endpoints import HomeEndpoint
from isabelle.piccolo_app import APP_CONFIG
from isabelle.tables import Event
from slack_bolt.adapter.starlette.async_handler import AsyncSlackRequestHandler
from isabelle.utils.slack import app 
from isabelle.utils import rsvp_checker

engine = None

async def open_database_connection_pool():
    global engine
    try:
        engine = engine_finder()
        await engine.start_connection_pool()
    except Exception:
        print("Unable to connect to the database")


async def close_database_connection_pool():
    global engine
    try:

        engine = engine_finder()
        await engine.close_connection_pool()
    except Exception:
        print("Unable to connect to the database")

async def health(req: Request):
    try:
        await app._async_client.api_test()
        slack_healthy = True
    except Exception:
        slack_healthy = False
    
    try:
        db_healthy = (await engine.get_version() is not None) if engine else False
    except Exception: 
        db_healthy = False

    return JSONResponse(
        {
            "healthy": slack_healthy and db_healthy,
            "slack": slack_healthy,
            "database": db_healthy,
        }
    )

@asynccontextmanager
async def lifespan(app: Starlette):
    await open_database_connection_pool()
    rsvp_checker.init()
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
                allowed_hosts=['isabelle.hackclub.com']
            ),
        ),
        Mount("/static/", StaticFiles(directory="static")),
        Mount("/events/", PiccoloCRUD(table=Event,read_only=True,page_size=255)),
        Route("/slack/events",endpoint=endpoint,methods=["POST"]),
        Route("/health",endpoint=health,methods=["GET"])
    ],
    lifespan=lifespan,
)
