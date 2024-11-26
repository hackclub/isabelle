from slack_bolt import App
from slack_sdk import WebClient

from .env import env
from events.buttons.create_event import handle_create_event_btn
from events.commands.create_event import handle_create_event_cmd
from events.views.create_event import handle_create_event_view
from events.buttons.propose_event import handle_propose_event_btn
from events.buttons.approve_event import handle_approve_event_btn
from events.buttons.rsvp import handle_rsvp_btn
from views.app_home import get_home

from typing import Any, Callable

app = App(token=env.slack_bot_token, signing_secret=env.slack_signing_secret)


@app.command("/create-event")
@app.command("/create-event-dev")
def create_event(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_create_event_cmd(ack, body, client)


@app.view("create_event")
@app.view("propose_event")
def create_event_view(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_create_event_view(ack, body, client)


@app.action("approve-event")
def approve_event(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_approve_event_btn(ack, body, client)


@app.event("app_home_opened")
def update_home_tab(client: WebClient, event: dict[str, Any]):
    user_id = event["user"]
    home_tab = get_home(user_id, client)
    client.views_publish(user_id=user_id, view=home_tab)


@app.action("create-event")
def create_event(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_create_event_btn(ack, body, client)


@app.action("propose-event")
def create_event(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_propose_event_btn(ack, body, client)


@app.action("add-to-gcal")
def add_to_gcal(ack: Callable):
    ack()


@app.action("rsvp")
def rsvp(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_rsvp_btn(ack, body, client)
