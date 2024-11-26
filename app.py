from utils.slack import app
from utils.env import env
from threading import Thread
from utils.rsvp_checker import rsvp_checker

if __name__ == "__main__":
    rsvp_thread = Thread(target=rsvp_checker, daemon=True)
    rsvp_thread.start()

    app.start(env.port)
