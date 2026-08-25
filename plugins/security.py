import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from config import Config
from database.db import get_security_settings, update_security_settings

# Group Security & Anti-Spam Listener
@Client.on_message(filters.group & ~filters.bot, group=2)
async def security_check_handler(bot: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Exclude Group Admins and Sudo Users
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ["owner", "administrator"] or user_id in Config.SUDO_USERS:
            return
    except Exception:
        pass

    # Fetch group security settings from Database
    settings = await get_security_settings(chat_id)
    
    # DEFAULT STATE: All protections are OFF (False) by default unless explicitly enabled
    link_protection = settings.get("link_protection", False) if settings else False
    forward_protection = settings.get("forward_protection", False) if settings else False
    username_protection = settings.get("username_protection", False) if settings else False

    is_violation = False
    violation_reason = ""

    # Check Link Protection (If Enabled by Admin)
    if link_protection and (message.entities or message.caption_entities):
        entities = message.entities or message.caption_entities
        for entity in entities:
            if entity.type in ["url", "text_link"]:
                is_violation = True
                violation_reason = "Sending Links is Restricted!"
                break

    # Check Forward Message Protection (If Enabled by Admin)
    if not is_violation and forward_protection and message.forward_date:
        is_violation = True
        violation_reason = "Forwarded Messages are Restricted!"

    # Check Username Protection (If Enabled by Admin)
    if not is_violation and username_protection and message.text:
        if "@" in message.text:
            is_violation = True
            violation_reason = "Telegram Usernames (@) are Restricted!"

    # If no rules are broken or all features are OFF, continue
    if not is_violation:
        return

    # Delete violating message instantly
    try:
        await message.delete()
    except Exception:
        pass

    # Warning Counter & Mute Logic (Remains 100% Intact)
    if not hasattr(bot, "user_warnings"):
        bot.user_warnings = {}

    user_key = f"{chat_id}_{user_id}"
    current_warns = bot.user_warnings.get(user_key, 0) + 1
    bot.user_warnings[user_key] = current_warns

    if not hasattr(bot, "sec_last_warnings"):
        bot.sec_last_warnings = {}

    old_warn = bot.sec_last_warnings.get(chat_id)
    if old_warn:
        try:
            await old_warn.delete()
        except Exception:
            pass

    if current_warns >= 3:
        try:
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=int(asyncio.get_event_loop().time() + 86400)
            )
            bot.user_warnings[user_key] = 0
            
            action_msg = await bot.send_message(
                chat_id=chat_id,
                text=(
                    f"🚫 <b>{message.from_user.mention} has been MUTED for 24 hours!</b>\n\n"
                    f"⚠️ <b>Reason:</b> Reached 3/3 Security Warnings.\n\n"
                    f"📢 <b>Powered by:</b> @official_botbox"
                ),
                disable_web_page_preview=True
            )
            bot.sec_last_warnings[chat_id] = action_msg
            return
        except Exception as e:
            print(f"Error muting user: {e}")

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
            disable_web_page_preview=True
        )
        bot.sec_last_warnings[chat_id] = sent_warn
    except Exception as e:
        print(f"Error sending security warning: {e}")
