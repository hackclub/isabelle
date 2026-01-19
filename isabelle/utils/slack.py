from typing import Any
from typing import Callable

from slack_bolt import App
from slack_sdk.web.async_client import AsyncWebClient

from isabelle.events.buttons.approve_event import handle_approve_event_btn
from isabelle.events.buttons.create_event import handle_create_event_btn
from isabelle.events.buttons.edit_event import handle_edit_event_btn
from isabelle.events.buttons.propose_event import handle_propose_event_btn
from isabelle.events.buttons.reject_event import handle_reject_event_btn
from isabelle.events.buttons.rsvp import handle_rsvp_btn
from isabelle.events.buttons.edit_ama_fields import handle_edit_ama_fields_btn
from isabelle.events.views.create_event import handle_create_event_view
from isabelle.events.views.edit_event import handle_edit_event_view
from isabelle.events.views.reject_event import handle_reject_event_view
from isabelle.events.views.close_edit_event import handle_close_edit_event
from isabelle.events.views.edit_ama_fields import handle_edit_ama_fields_view
from isabelle.events.shortcuts.set_rsvp_msg import handle_set_rsvp_msg
from isabelle.events.views.rsvp_msg_set_response import handle_rsvp_msg_set_response
from isabelle.events.reaction_added import handle_reaction_added
from isabelle.events.reaction_removed import handle_reaction_removed
from isabelle.utils.env import env
from isabelle.views.app_home import get_home
from slack_bolt.async_app import AsyncApp

app = AsyncApp(token=env.slack_bot_token, signing_secret=env.slack_signing_secret)


@app.view("create_event")
@app.view("propose_event")
async def create_event_view(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await handle_create_event_view(ack, body, client)


@app.view("edit_event")
async def edit_event_view(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await handle_edit_event_view(ack, body, client)


@app.view("reject_event")
async def reject_event_view(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await handle_reject_event_view(ack, body, client)


@app.action("approve-event")
async def approve_event(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await handle_approve_event_btn(ack, body, client)


@app.action("reject-event")
async def reject_event(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await handle_reject_event_btn(ack, body, client)


@app.event("app_home_opened")
async def update_home_tab(client: AsyncWebClient, event: dict[str, Any]):
    user_id = event["user"]
    home_tab = await get_home(user_id, client)
    await client.views_publish(user_id=user_id, view=home_tab)


@app.action("create-event")
async def create_event_btn(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await handle_create_event_btn(ack, body, client)


@app.action("edit-event")
async def edit_event(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await handle_edit_event_btn(ack, body, client)


@app.action("propose-event")
async def create_event(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await handle_propose_event_btn(ack, body, client)


@app.action("add-to-gcal")
async def add_to_gcal(ack: Callable):
    await ack()


@app.action("rsvp")
async def rsvp(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await handle_rsvp_btn(ack, body, client)

@app.shortcut("set_rsvp_msg")
async def set_rsvp_msg(ack: Callable, shortcut, body, client: AsyncWebClient):
    await handle_set_rsvp_msg(ack, shortcut, body, client)

@app.view("rsvp_msg_set_response")
async def rsvp_msg_set_response(ack, body, view, client):
    await handle_rsvp_msg_set_response(ack, body, view, client)

@app.event("reaction_added")
async def reaction_added(body, client):
    await handle_reaction_added(body, client)

@app.event("reaction_removed")
async def reaction_removed(body, client):
    await handle_reaction_removed(body, client)

@app.view_closed("edit_event")
async def close_edit_event(ack, body, client):
    await handle_close_edit_event(ack, body, client)


@app.action("edit-ama-fields")
async def edit_ama_fields_btn(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await handle_edit_ama_fields_btn(ack, body, client)

@app.view("edit_ama_fields")
async def edit_ama_fields_view(ack: Callable, body: dict[str, Any], client: AsyncWebClient):
    await handle_edit_ama_fields_view(ack, body, client)