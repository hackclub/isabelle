from typing import Any
from typing import Callable

from slack_bolt import App
from slack_sdk import WebClient

from isabelle.events.buttons.approve_event import handle_approve_event_btn
from isabelle.events.buttons.create_event import handle_create_event_btn
from isabelle.events.buttons.edit_event import handle_edit_event_btn
from isabelle.events.buttons.propose_event import handle_propose_event_btn
from isabelle.events.buttons.reject_event import handle_reject_event_btn
from isabelle.events.buttons.rsvp import handle_rsvp_btn
from isabelle.events.views.create_event import handle_create_event_view
from isabelle.events.views.edit_event import handle_edit_event_view
from isabelle.events.views.reject_event import handle_reject_event_view
from isabelle.events.shortcuts.set_rsvp_msg import handle_set_rsvp_msg
from isabelle.events.views.rsvp_msg_set_response import handle_rsvp_msg_set_response
from isabelle.events.reaction_added import handle_reaction_added
from isabelle.utils.env import env
from isabelle.views.app_home import get_home

app = App(token=env.slack_bot_token, signing_secret=env.slack_signing_secret)


@app.view("create_event")
@app.view("propose_event")
def create_event_view(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_create_event_view(ack, body, client)


@app.view("edit_event")
def edit_event_view(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_edit_event_view(ack, body, client)


@app.view("reject_event")
def reject_event_view(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_reject_event_view(ack, body, client)


@app.action("approve-event")
def approve_event(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_approve_event_btn(ack, body, client)


@app.action("reject-event")
def reject_event(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_reject_event_btn(ack, body, client)


@app.event("app_home_opened")
def update_home_tab(client: WebClient, event: dict[str, Any]):
    user_id = event["user"]
    home_tab = get_home(user_id, client)
    client.views_publish(user_id=user_id, view=home_tab)


@app.action("create-event")
def create_event_btn(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_create_event_btn(ack, body, client)


@app.action("edit-event")
def edit_event(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_edit_event_btn(ack, body, client)


@app.action("propose-event")
def create_event(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_propose_event_btn(ack, body, client)


@app.action("add-to-gcal")
def add_to_gcal(ack: Callable):
    ack()


@app.action("rsvp")
def rsvp(ack: Callable, body: dict[str, Any], client: WebClient):
    handle_rsvp_btn(ack, body, client)

@app.shortcut("set_rsvp_msg")
def set_rsvp_msg(ack: Callable, shortcut, body, client: WebClient):
    handle_set_rsvp_msg(ack, shortcut, body, client)

@app.view("rsvp_msg_set_response")
def rsvp_msg_set_response(ack, body, view, client):
    handle_rsvp_msg_set_response(ack, body, view, client)

@app.event("reaction_added")
def reaction_added(body, client):
    handle_reaction_added(body, client)