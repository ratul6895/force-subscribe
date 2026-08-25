import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from pyrogram.enums import ChatMemberStatus
from config import Config

OFFICIAL_CHANNEL = "https://t.me/official_botbox"

# 1. Regex Patterns for Links and Usernames
URL_PATTERN = re.compile(r"(https?://\S+|www\.\S+|\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b)")
USERNAME_PATTERN = re.compile(r"(@[a-zA-Z0-9_]{4,})|(t\.me/[a-zA-Z0-9_]{4,})")

@Client.on_message(filters.group & ~filters.bot, group=2)
async def group_security_handler(bot: Client, message: Message):
    if not message.from_user:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # Exclude Group Admins, Owners, and Sudo Users
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR] or user_id in Config.SUDO_USERS:
            return
    except Exception:
        pass

    violation_reason = None

    # Check 1: Anti-Forward
    if message.forward_date or message.forward_from or message.forward_from_chat:
        violation_reason = "Forwarding messages from other chats is not allowed!"

    # Check 2: Anti-Link / Anti-URL
    elif message.text and URL_PATTERN.search(message.text):
        violation_reason = "Sending external links/URLs is strictly prohibited!"

    # Check 3: Anti-Username / Mentions
    elif message.text and USERNAME_PATTERN.search(message.text):
        violation_reason = "Sharing @usernames or Telegram channels is not allowed!"

    # If no violation found, pass
    if not violation_reason:
        return

    # Delete the offending message immediately
    try:
        await message.delete()
    except Exception:
        pass

    # Initialize Memory Trackers inside bot instance
    if not hasattr(bot, "user_warnings"):
        bot.user_warnings = {}
    if not hasattr(bot, "sec_last_warnings"):
        bot.sec_last_warnings = {}

    user_key = f"{chat_id}_{user_id}"
    current_warns = bot.user_warnings.get(user_key, 0) + 1
    bot.user_warnings[user_key] = current_warns

    # Delete previous security warning message in this group if exists
    if chat_id in bot.sec_last_warnings:
        try:
            await bot.sec_last_warnings[chat_id].delete()
        except Exception:
            pass

    bot_obj = await bot.get_me()

    # ACTION: If warnings reach 3, MUTE the user for 24 Hours
    if current_warns >= 3:
        try:
            # Mute user for 24 hours (86400 seconds)
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=int(asyncio.get_event_loop().time() + 86400)
            )
            bot.user_warnings[user_key] = 0 # Reset warnings
            
            action_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Official Channel", url=OFFICIAL_CHANNEL)]
            ])
            
            action_msg = await bot.send_message(
                chat_id=chat_id,
                text=(
                    f"🚫 <b>{message.from_user.mention} has been MUTED for 24 hours!</b>\n\n"
                    f"⚠️ <b>Reason:</b> Reached 3/3 Security Warnings.\n"
                    f"📢 <b>Updates & Support:</b> @official_botbox"
                ),
                reply_markup=action_markup,
                disable_web_page_preview=True
            )
            bot.sec_last_warnings[chat_id] = action_msg
            return
        except Exception as e:
            print(f"Error muting user: {e}")

    # WARNING MESSAGE: 1/3 or 2/3
    warn_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Official Channel", url=OFFICIAL_CHANNEL),
            InlineKeyboardButton("➕ Add Me to Group", url=f"https://t.me/{bot_obj.username}?startgroup=true")
        ]
    ])

    warn_text = (
        f"⚠️ <b>Security Alert for {message.from_user.mention}!</b>\n\n"
        f"🛑 <b>Rule Broken:</b> {violation_reason}\n"
        f"📊 <b>Warning Count:</b> [{current_warns}/3]\n"
        f"💡 <i>Reaching 3/3 warnings will result in a 24-hour mute!</i>\n\n"
        f"📢 <b>Powered by:</b> @official_botbox"
    )

    try:
        sent_warn = await bot.send_message(
            chat_id=chat_id,
            text=warn_text,
            reply_markup=warn_markup,
            disable_web_page_preview=True
        )
        bot.sec_last_warnings[chat_id] = sent_warn
    except Exception as e:
        print(f"Error sending security warning: {e}")
