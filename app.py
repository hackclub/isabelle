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

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware

#For RateLimiting

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self,app,max_requests: int=100, window_seconds: int =60 ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = {}
    
    async def dispatch(self,request: Request, call_next):
        if not request.url.path.startswith("/events"):
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        if client_ip in self._requests:
            self._requests[client_ip] = [
                ts for ts in self._requests[client_ip]
                if now - ts < self.window_seconds
            ]
        else:
            self._requests[client_ip]=[]

        #Rate Limit checking

        if len(self._requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                {"error": "Rate limit exceeded. Try again later."},
                status_code=429
            )
        self._requests[client_ip].append(now)
        return await call_next(request)




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
        Route("/health",endpoint=health,methods=["GET"])
    ],
    lifespan=lifespan,
    middleware=[Middleware(RateLimitMiddleware,max_requests=100,window_seconds = 60)]
)
