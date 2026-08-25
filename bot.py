import asyncio
from pyrogram import Client, idle
from config import Config
from web import web_server
from aiohttp import web

class Bot(Client):
    def __init__(self):
        super().__init__(
            "ForceSubscribeBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins")
        )

    async def start(self):
        await super().start()
        print("Bot Started Successfully!")
        
        # Render Port Binding (Fixing No Open Ports Error)
        app = web.AppRunner(await web_server())
        await app.setup()
        port = int(Config.PORT)
        site = web.TCPSite(app, "0.0.0.0", port)
        await site.start()
        print(f"Web Server running on port {port}")
        
        # Keep the bot running continuously on Render
        await idle()

    async def stop(self, *args):
        await super().stop()
        print("Bot Stopped.")

if __name__ == "__main__":
    bot = Bot()
    bot.run()
