import os
from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is Alive and Running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    return app
