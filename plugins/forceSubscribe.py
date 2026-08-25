import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant, FloodWait, InputUserDeactivated, UserIsBlocked, ChatAdminRequired
from config import Config, Messages
from database.db import get_channel, add_channel, dischannel, add_chat, get_chats_by_type

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(bot: Client, message: Message):
    await add_chat(message.from_user.id, "user")
    bot_obj = await bot.get_me()
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Me to Your Group", url=f"https://t.me/{bot_obj.username}?startgroup=true"),
            InlineKeyboardButton("📖 Help & Commands", callback_data="help_cmd")
        ]
    ])
    text = Messages.START_MSG.format(message.from_user.first_name, message.from_user.id)
    await message.reply_text(text, reply_markup=keyboard, disable_web_page_preview=True)

@Client.on_callback_query(filters.regex("help_cmd"))
async def help_callback(bot: Client, query):
    bot_obj = await bot.get_me()
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Back to Home", callback_data="home_cmd"),
            InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_obj.username}?startgroup=true")
        ]
    ])
    await query.message.edit_text(Messages.HELP_MSG, reply_markup=keyboard, disable_web_page_preview=True)

@Client.on_callback_query(filters.regex("home_cmd"))
async def home_callback(bot: Client, query):
    bot_obj = await bot.get_me()
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Me to Your Group", url=f"https://t.me/{bot_obj.username}?startgroup=true"),
            InlineKeyboardButton("📖 Help & Commands", callback_data="help_cmd")
        ]
    ])
    text = Messages.START_MSG.format(query.from_user.first_name, query.from_user.id)
    await query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)

@Client.on_message(filters.command(["forcesubscribe", "fsub"]) & filters.group)
async def set_fsub(bot: Client, message: Message):
    await add_chat(message.chat.id, "group")
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR] and message.from_user.id not in Config.SUDO_USERS:
        return await message.reply_text("❌ This command is only for Group Admins!")

    if len(message.command) < 2:
        curr_chan = await get_channel(message.chat.id)
        if curr_chan:
            return await message.reply_text(f"📢 **Current FSub Channel:** {curr_chan}")
        return await message.reply_text("⚠️ **Usage:**\n`/fsub @YourChannel` or `/fsub off` to disable.")

    arg = message.command[1].lower()
    if arg in ["no", "off", "disable"]:
        await dischannel(message.chat.id)
        return await message.reply_text("✅ **Force Subscribe disabled successfully.**")

    channel = message.command[1]
    await add_channel(message.chat.id, channel)
    await message.reply_text(f"✅ **Force Subscribe Channel set to:** {channel}")

@Client.on_message(filters.group & ~filters.bot, group=-1)
async def check_subscription(bot: Client, message: Message):
    await add_chat(message.chat.id, "group")
    channel = await get_channel(message.chat.id)
    if not channel:
        return

    # Check Admin & Sudo Exemption
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR] or message.from_user.id in Config.SUDO_USERS:
            return
    except Exception:
        pass

    clean_channel = channel.replace("https://t.me/", "").replace("@", "")

    try:
        user = await bot.get_chat_member(clean_channel, message.from_user.id)
        if user.status == ChatMemberStatus.BANNED:
            await message.delete()
    except UserNotParticipant:
        # INSTANT DELETE FOR NON-SUBSCRIBERS
        try:
            await message.delete()
        except Exception:
            pass

        bot_obj = await bot.get_me()
        channel_url = channel if channel.startswith("http") else f"https://t.me/{clean_channel}"
        
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=channel_url)],
            [InlineKeyboardButton("➕ Add Me to Your Group", url=f"https://t.me/{bot_obj.username}?startgroup=true")]
        ])

        warn_msg = await message.reply_text(
            f"⚠️ <b>{message.from_user.mention}</b>, you must join our channel to send messages in this group!",
            reply_markup=markup
        )
        await asyncio.sleep(8)
        try:
            await warn_msg.delete()
        except Exception:
            pass
    except Exception as e:
        print(f"Error: {e}")

@Client.on_message(filters.command("broadcast") & filters.user(Config.SUDO_USERS))
async def safe_broadcast(bot: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to any message with `/broadcast user` or `/broadcast group`.")

    target = message.command[1] if len(message.command) > 1 else "user"
    if target not in ["user", "group"]:
        return await message.reply_text("⚠️ **Usage:** `/broadcast user` or `/broadcast group`")

    targets = await get_chats_by_type(target)
    sent, failed = 0, 0
    status = await message.reply_text(f"📢 **Starting {target.capitalize()} Broadcast...**")

    for cid in targets:
        try:
            await message.reply_to_message.copy(cid)
            sent += 1
            await asyncio.sleep(0.05)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            await message.reply_to_message.copy(cid)
            sent += 1
        except (InputUserDeactivated, UserIsBlocked, ChatAdminRequired):
            failed += 1
        except Exception:
            failed += 1

    await status.edit_text(f"✅ **Broadcast Completed!**\n\n🎯 Target: {target}\n🟢 Success: {sent}\n🔴 Failed: {failed}")
