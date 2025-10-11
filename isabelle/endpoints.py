
from starlette.endpoints import HTTPEndpoint
from starlette.responses import PlainTextResponse




class HomeEndpoint(HTTPEndpoint):
    async def get(self, request):


        return PlainTextResponse("Hello! Isabelle here")
