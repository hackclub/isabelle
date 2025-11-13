# ATTENTION
# This entry point is now only for the slack app development. The whole app entrypoint is in /main.py now
import sentry_sdk
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from isabelle.utils.env import env
import isabelle.utils.rsvp_checker as rspv_checker
from isabelle.utils.slack import app
# from isabelle.utils.rsvp_checker import rsvp_checker


async def start():
    # disable sentry and rsvp_checker since this will only be used in socket mode
    
    #sentry_sdk.init(dsn=env.sentry_dsn, traces_sample_rate=1.0)
    #sentry_sdk.profiler.start_profiler()
    rspv_checker.init()

    if env.slack_app_token is not None:
        handler = AsyncSocketModeHandler(app, env.slack_app_token)
        await handler.start_async()
    else:
        app.start(env.port)


if __name__ == "__main__":
    import asyncio
    asyncio.run(start())
