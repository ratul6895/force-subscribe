import os
import asyncio
from aiohttp import web
from pyrogram import Client, __version__
from config import Config
from database.db import db

# ------------------ WEB SERVER FOR RENDER ------------------ #
# Render বা হোস্ট প্ল্যাটফর্মে বট সচল রাখতে হালকা ওয়েব সার্ভার
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({
        "status": "online",
        "bot": "Force Subscribe Bot",
        "version": "2.0.0",
        "language": "Bangla"
    })

async def web_server():
    web_app = web.Application()
    web_app.add_routes(routes)
    return web_app


# ------------------ BOT CLIENT INITIALIZATION ------------------ #
class Bot(Client):
    def __init__(self):
        super().__init__(
            name="ForceSubscribeBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins")
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.mention = me.mention
        self.username = me.username
        
        print(f"==========================================")
        print(f"🤖 বট সফলভাবে চালু হয়েছে: @{me.username}")
        print(f"⚡ Pyrogram Version: {__version__}")
        print(f"✨ ভাষা স্টাইল: বাংলা (Bangla Font UI)")
        print(f"==========================================")

        # Web Server Start (Port binding for Render)
        app = web.AppRunner(await web_server())
        await app.setup()
        port = int(Config.PORT)
        await web.TCPSite(app, "0.0.0.0", port).start()
        print(f"🌐 Web Server Running on Port: {port}")

    async def stop(self, *args):
        await super().stop()
        print("🛑 বট বন্ধ করা হয়েছে।")

if __name__ == "__main__":
    bot = Bot()
    bot.run()
