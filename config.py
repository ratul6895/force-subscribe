import os

class Config:
    API_ID = int(os.environ.get("API_ID", "12345"))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    MONGO_DB_URI = os.environ.get("MONGO_DB_URI", "")
    PORT = os.environ.get("PORT", "8080")
    SUDO_USERS = [int(x) for x in os.environ.get("SUDO_USERS", "").split()]

class Messages:
    START_MSG = """
✨ **Welcome to Force Subscribe Bot!**

Hello **{}** [<code>{}</code>] 👋

I am an advanced Force Subscribe management bot. I can force users to join your target channel before chatting in your group!

⚡ **Features:**
• Instant & Automatic Message Deletion
• Clean & Interactive UI Buttons
• Advanced Group Subscription Control
"""

    HELP_MSG = """
📖 **Bot Command Guide & Instructions**

<b>👤 User Commands:</b>
└ <code>/start</code> - Check bot online status & main menu.

<b>👥 Group Admin Commands:</b>
└ <code>/fsub @YourChannel</code> - Connect channel for Force Subscribe.
└ <code>/fsub off</code> - Disable Force Subscribe in the group.
└ <code>/fsub</code> - Check currently configured channel.

⚠️ *Note: Make sure to make the bot an Admin with delete permissions in your Group & Channel!*
"""
