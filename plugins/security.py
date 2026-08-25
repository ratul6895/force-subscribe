import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatMemberStatus
from config import Config
from database.db import get_security_settings, update_security_settings

# 1. Admin Commands to Toggle Security Features On/Off
@Client.on_message(filters.command(["antilink", "antiforward", "antiusername"]) & filters.group)
async def toggle_security_cmd(bot: Client, message: Message):
    # Check Admin Permission
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR] and message.from_user.id not in Config.SUDO_USERS:
        return await message.reply_text("❌ **Access Denied:** Only Group Admins can change security settings!")

    if len(message.command) < 2:
        return await message.reply_text(
            f"⚠️ **Usage:** `/{message.command[0]} on` or `/{message.command[0]} off`"
        )

    cmd = message.command[0].lower()
    option = message.command[1].lower()

    if option not in ["on", "off"]:
        return await message.reply_text("⚠️ Invalid Option! Use `on` or `off`.")

    status = True if option == "on" else False
    
    key_map = {
        "antilink": ("link_protection", "Anti-Link"),
        "antiforward": ("forward_protection", "Anti-Forward"),
        "antiusername": ("username_protection", "Anti-Username")
    }

    setting_key, feature_name = key_map[cmd]
    await update_security_settings(message.chat.id, setting_key, status)
    
    state_text = "🟢 **ENABLED**" if status else "🔴 **DISABLED**"
    await message.reply_text(f"⚙️ **{feature_name} Protection** is now {state_text} for this group!")

# 2. View Live Security Status in Group
@Client.on_message(filters.command(["secstatus", "security"]) & filters.group)
async def view_security_status(bot: Client, message: Message):
    settings = await get_security_settings(message.chat.id)
    
    l_status = "🟢 ON" if settings.get("link_protection", False) else "🔴 OFF (Default)"
    f_status = "🟢 ON" if settings.get("forward_protection", False) else "🔴 OFF (Default)"
    u_status = "🟢 ON" if settings.get("username_protection", False) else "🔴 OFF (Default)"

    text = (
        f"🛡️ <b>Group Security Settings for {message.chat.title}:</b>\n\n"
        f"🔗 <b>Anti-Link:</b> {l_status}\n"
        f"↩️ <b>Anti-Forward:</b> {f_status}\n"
        f"🏷️ <b>Anti-Username (@):</b> {u_status}\n\n"
        "💡 <i>Admins can toggle using <code>/antilink on/off</code>, <code>/antiforward on/off</code>, <code>/antiusername on/off</code></i>"
    )
    await message.reply_text(text, disable_web_page_preview=True)

# 3. Main Security Listener Filter
@Client.on_message(filters.group & ~filters.bot, group=2)
async def security_check_handler(bot: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Exclude Group Admins and Sudo Users
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR] or user_id in Config.SUDO_USERS:
            return
    except Exception:
        pass

    # Fetch settings (Defaults to False/Off if not set)
    settings = await get_security_settings(chat_id)
    link_prot = settings.get("link_protection", False)
    fwd_prot = settings.get("forward_protection", False)
    user_prot = settings.get("username_protection", False)

    is_violation = False
    violation_reason = ""

    # Link Check (Only if Enabled)
    if link_prot and (message.entities or message.caption_entities):
        entities = message.entities or message.caption_entities
        for entity in entities:
            if entity.type in ["url", "text_link"]:
                is_violation = True
                violation_reason = "Sending Links is Restricted!"
                break

    # Forward Check (Only if Enabled)
    if not is_violation and fwd_prot and message.forward_date:
        is_violation = True
        violation_reason = "Forwarded Messages are Restricted!"

    # Username Check (Only if Enabled)
    if not is_violation and user_prot and message.text and "@" in message.text:
        is_violation = True
        violation_reason = "Telegram Usernames (@) are Restricted!"

    if not is_violation:
        return

    # Delete violating message
    try:
        await message.delete()
    except Exception:
        pass

    # Warning & Dynamic Mute Handler
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
        print(f"Error sending warning: {e}")
