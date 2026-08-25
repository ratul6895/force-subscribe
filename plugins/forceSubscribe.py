import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import UserNotParticipant, FloodWait, InputUserDeactivated, UserIsBlocked, ChatAdminRequired
from config import Config, Messages
from database.db import get_channel, add_channel, dischannel, add_chat, get_chats_by_type

OFFICIAL_CHANNEL = "https://t.me/official_botbox"

# 1. Automatic Message when Bot is Added to a New Group
@Client.on_message(filters.new_chat_members)
async def bot_added_to_group(bot: Client, message: Message):
    bot_obj = await bot.get_me()
    for member in message.new_chat_members:
        if member.id == bot_obj.id:
            await add_chat(message.chat.id, "group")
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📢 Official Channel", url=OFFICIAL_CHANNEL),
                    InlineKeyboardButton("📖 Commands Guide", callback_data="help_cmd")
                ]
            ])
            
            welcome_text = f"""
✨ **Hello Everyone in {message.chat.title}!** 👋

Thanks for adding me here! I am your **Force Subscribe Manager**.

⚙️ **Quick Setup Guide:**
1️⃣ Make me an **Admin** with delete permissions in this group.
2. Add me as an **Admin** in your target channel.
3️⃣ Send the command below in this group to activate:

👉 **Example:** <code>/fsub @YourChannelUsername</code>
💡 **Disable FSub:** <code>/fsub off</code>

Need more help? Click the button below! 🚀
"""
            await message.reply_text(welcome_text, reply_markup=keyboard, disable_web_page_preview=True)

# 2. Private Start Command
@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(bot: Client, message: Message):
    await add_chat(message.from_user.id, "user")
    bot_obj = await bot.get_me()
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Me to Your Group", url=f"https://t.me/{bot_obj.username}?startgroup=true")
        ],
        [
            InlineKeyboardButton("📢 Official Channel", url=OFFICIAL_CHANNEL),
            InlineKeyboardButton("📖 Help & Commands", callback_data="help_cmd")
        ]
    ])
    text = Messages.START_MSG.format(message.from_user.first_name, message.from_user.id)
    await message.reply_text(text, reply_markup=keyboard, disable_web_page_preview=True)

# 3. Callback Handlers
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
            InlineKeyboardButton("➕ Add Me to Your Group", url=f"https://t.me/{bot_obj.username}?startgroup=true")
        ],
        [
            InlineKeyboardButton("📢 Official Channel", url=OFFICIAL_CHANNEL),
            InlineKeyboardButton("📖 Help & Commands", callback_data="help_cmd")
        ]
    ])
    text = Messages.START_MSG.format(query.from_user.first_name, query.from_user.id)
    await query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)

# 4. Group Force Subscribe Setup Command
@Client.on_message(filters.command(["forcesubscribe", "fsub"]) & filters.group)
async def set_fsub(bot: Client, message: Message):
    await add_chat(message.chat.id, "group")
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR] and message.from_user.id not in Config.SUDO_USERS:
        return await message.reply_text("❌ **Access Denied:** This command is restricted to Group Admins only!")

    if len(message.command) < 2:
        curr_chan = await get_channel(message.chat.id)
        if curr_chan:
            return await message.reply_text(f"📢 **Current Connected Channel:** `{curr_chan}`")
        return await message.reply_text(
            "⚠️ **Incorrect Usage!**\n\n"
            "👉 **To Setup Channel:** `/fsub @YourChannel`\n"
            "👉 **To Turn Off FSub:** `/fsub off`"
        )

    arg = message.command[1].lower()
    if arg in ["no", "off", "disable"]:
        await dischannel(message.chat.id)
        return await message.reply_text("✅ **Force Subscribe Service has been Disabled for this Group.**")

    channel = message.command[1]
    await add_channel(message.chat.id, channel)
    await message.reply_text(
        f"🎯 **Force Subscribe Activated Successfully!**\n\n"
        f"📢 **Target Channel:** `{channel}`\n"
        f"🔒 *Unsubscribed members will be restricted from messaging.*"
    )

# 5. Group Message Listener (Instant Delete & Restriction)
@Client.on_message(filters.group & ~filters.bot, group=-1)
async def check_subscription(bot: Client, message: Message):
    await add_chat(message.chat.id, "group")
    channel = await get_channel(message.chat.id)
    if not channel:
        return

    # Exclude Group Admins and Sudo Users
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
        # Instant Message Deletion
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
            f"🚫 <b>{message.from_user.mention}</b>, you must join our official channel to send messages here!",
            reply_markup=markup
        )
        await asyncio.sleep(8)
        try:
            await warn_msg.delete()
        except Exception:
            pass
    except Exception as e:
        print(f"Error: {e}")

# 6. Hidden Broadcast Command for Sudos
@Client.on_message(filters.command("broadcast") & filters.user(Config.SUDO_USERS))
async def safe_broadcast(bot: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to any message with `/broadcast user` or `/broadcast group`.")

    target = message.command[1] if len(message.command) > 1 else "user"
    if target not in ["user", "group"]:
        return await message.reply_text("⚠️ **Usage:** `/broadcast user` or `/broadcast group`")

    targets = await get_chats_by_type(target)
    sent, failed = 0, 0
    status = await message.reply_text(f"🚀 **Starting {target.capitalize()} Broadcast Process...**")

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

    await status.edit_text(f"✅ **Broadcast Task Completed!**\n\n🎯 **Target:** `{target}`\n🟢 **Success:** `{sent}`\n🔴 **Failed:** `{failed}`")
