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
import logging
import secrets
from isabelle.utils.env import env

def _check_internal_secret(req: Request) -> bool:
    provided = req.headers.get("x-internal-secret", "")
    return secrets.compare_digest(provided, env.events_rsvp_secret)

async def internal_rsvp(req: Request):
    if not _check_internal_secret(req):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    event_id = req.path_params["event_id"]
    body = await req.json()
    slack_id = body.get("slack_id")
    attending = body.get("attending")
    user_info = body.get("user_info")

    if not slack_id or not isinstance(attending, bool):
        return JSONResponse({"error": "slack_id and boolean attending required"}, status_code=422)
    
    if user_info and attending:
        try:
            slack_user = await app._async_client.users_info(user=slack_id)
            profile = slack_user["user"]["profile"]
            user_info["slackDisplayName"] = (
                profile.get("display_name")
                or profile.get("real_name")
                or None
            )
        except Exception as e:
            logging.warning("Could not resolve slack display name for %s: %s", slack_id, e)
            user_info["slackDisplayName"] = None

    event = await env.database.toggle_user_interest(event_id, slack_id, forced_state=attending,user_info=user_info,)
    if not event:
        return JSONResponse({"error": "event not found or update failed"}, status_code=404)
    if isinstance(event, dict):
        interested = event.get("InterestedUsers") or []
        count = event.get("InterestCount", 0)
    else:
        interested = event.InterestedUsers or []
        count = event.InterestCount or 0

    rsvp_data = event.get("RSVPData") or {}
    legacy_users = (event.get("InterestedUsers") or []) if isinstance(event, dict) else (event.InterestedUsers or [])
    sub = (user_info or {}).get("sub")
    in_rsvp = (sub and sub in rsvp_data) or any (
        v.get("slackId") == slack_id for v in rsvp_data.values()
    )
    is_attending = in_rsvp or (slack_id in legacy_users)
    return JSONResponse({ "attending": is_attending, "InterestCount": count })
async def internal_rsvp_list(req: Request):
    if not _check_internal_secret(req):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    event_id = req.path_params["event_id"]
    event = await env.database.get_event(event_id)
    if not event:
        return JSONResponse({"error": "event not found"}, status_code=404)
    
    legacy_users: list = list(event.get("InterestedUsers") or [])
    rsvp_data: dict = dict(event.get("RSVPData") or {})
    rsvp_slack_ids = {v.get("slackId") for v in rsvp_data.values() if v.get("slackId")}
    for slack_id in legacy_users:
        if slack_id not in rsvp_slack_ids:
            rsvp_data[slack_id] = {
                "sub": None,
                "slackId": slack_id,
                "name": None,
                "email": None,
                "slackDisplayName": None,
                "rsvpedAt": None
            }
    return JSONResponse({ "attendees": list(rsvp_data.values()), "InterestCount": event.get("InterestCount", 0) })

engine = None

async def open_database_connection_pool():
    global engine
    try:
        engine = engine_finder()
        await engine.start_connection_pool()
    except Exception:
        logging.error("Unable to connect to the database")


async def close_database_connection_pool():
    global engine
    try:

        engine = engine_finder()
        await engine.close_connection_pool()
    except Exception:
        logging.error("Unable to close the connection to the database")

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
    if not env.testing:
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
        Mount("/events/", PiccoloCRUD(table=Event,read_only=True,page_size=1000)),
        Route("/slack/events",endpoint=endpoint,methods=["POST"]),
        Route("/health",endpoint=health,methods=["GET"]),
        Route("/internal/events/{event_id}/rsvp", endpoint=internal_rsvp, methods=["PUT"]),
        Route("/internal/events/{event_id}/rsvps", endpoint=internal_rsvp_list, methods=["GET"]),
    ],
    lifespan=lifespan,
)
