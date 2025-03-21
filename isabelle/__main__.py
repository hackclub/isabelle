from isabelle.utils.slack import app
from isabelle.utils.env import env
from threading import Thread
from isabelle.utils.rsvp_checker import rsvp_checker
import sentry_sdk

def start():
    sentry_sdk.init(dsn=env.sentry_dsn, traces_sample_rate=1.0)
    sentry_sdk.profiler.start_profiler()
    rsvp_thread = Thread(target=rsvp_checker, daemon=True)
    rsvp_thread.start()

    app.start(env.port)

if __name__ == "__main__":
    start()
