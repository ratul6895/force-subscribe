import asyncio
from pyrogram import Client
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
        
        # Web Server setup for Render
        app = web.AppRunner(await web_server())
        await app.setup()
        port = int(Config.PORT)
        site = web.TCPSite(app, "0.0.0.0", port)
        await site.start()

    async def stop(self, *args):
        await super().stop()
        print("Bot Stopped.")

if __name__ == "__main__":
    bot = Bot()
    
    # Simple web server runner along with Pyrogram bot
    async def run_bot():
        await bot.start()
        await asyncio.Event().wait()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_bot())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        loop.run_until_complete(bot.stop())
