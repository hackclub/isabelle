
from starlette.endpoints import HTTPEndpoint
from starlette.responses import PlainTextResponse

import json
import logging
from isabelle.utils.env import env
from starlette.responses import JSONResponse
from starlette.requests import Request


class HomeEndpoint(HTTPEndpoint):
    async def get(self, request):


        return PlainTextResponse("Hello! Isabelle (REST API) here. https://hack.club/gh/isabelle")

async def rsvp_endpoint(request: Request):
    if request.method !="POST":
        return JSONResponse({"error": "Method not allowed"},status_code=405)
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"},status_code=400)
    
    event_id = body.get("event_id")
    user_id = body.get("user_id")

    if not event_id:
        return JSONResponse({"error":"Missing event_id"},status_code=400)
    if not user_id:
        return JSONResponse({"error": "Internal server error"},status_code=400)
    try:
        event = await env.database.toggle_user_interest(event_id,user_id)   
    except Exception as e:
        logging.error(f"Error toggling RSVP: {e}")
        return JSONResponse({"error": "Internal server error"},status_code=500)
    if not event:
        return JSONResponse({"error": "Event not found"},status_code=404)

    interested_users = list(event.InterestedUsers or [])
    is_interested =  user_id in interested_users

    return JSONResponse({
        "event_id": str(event.id),
        "user_id": user_id,
        "is_interested": is_interested,
        "interest_count": event.InterestCount,
    })
