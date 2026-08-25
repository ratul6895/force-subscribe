import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant, FloodWait, InputUserDeactivated, UserIsBlocked, ChatAdminRequired
from config import Config, Messages
from database import get_channel, add_channel, dischannel, add_chat, get_chats_by_type

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(bot: Client, message: Message):
    await add_chat(message.from_user.id, "user")
    text = Messages.START_MSG.format(message.from_user.first_name, message.from_user.id)
    await message.reply_text(text, disable_web_page_preview=False)

@Client.on_message(filters.command(["forcesubscribe", "fsub"]) & filters.group)
async def set_fsub(bot: Client, message: Message):
    await add_chat(message.chat.id, "group")
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR] and message.from_user.id not in Config.SUDO_USERS:
        return await message.reply_text("❌ এই কমান্ডটি শুধু গ্রুপের অ্যাডমিনদের জন্য।")

    if len(message.command) < 2:
        curr_chan = await get_channel(message.chat.id)
        if curr_chan:
            return await message.reply_text(f"📢 বর্তমান সেটআপ করা চ্যানেল: {curr_chan}")
        return await message.reply_text("⚠️ ব্যবহার পদ্ধতি:\n`/fsub @YourChannel` অথবা `/fsub off` (বন্ধ করার জন্য)")

    arg = message.command[1].lower()
    if arg in ["no", "off", "disable"]:
        await dischannel(message.chat.id)
        return await message.reply_text("✅ Force Subscribe ফিচারটি বন্ধ করা হয়েছে।")

    channel = message.command[1]
    await add_channel(message.chat.id, channel)
    await message.reply_text(f"✅ সফলভাবে চ্যানেল যুক্ত হয়েছে!\nচ্যানেল: {channel}")

@Client.on_message(filters.group & ~filters.bot, group=-1)
async def check_subscription(bot: Client, message: Message):
    await add_chat(message.chat.id, "group")
    channel = await get_channel(message.chat.id)
    if not channel:
        return

    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR] or message.from_user.id in Config.SUDO_USERS:
            return
    except:
        pass

    try:
        clean_channel = channel.replace("https://t.me/", "").replace("@", "")
        user = await bot.get_chat_member(clean_channel, message.from_user.id)
        if user.status == ChatMemberStatus.BANNED:
            await message.delete()
    except UserNotParticipant:
        try:
            await message.delete()
        except Exception:
            pass

        channel_url = channel if channel.startswith("http") else f"https://t.me/{clean_channel}"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("📢 চ্যানেলে যুক্ত হন", url=channel_url)]])
        
        warn_msg = await message.reply_text(
            f"⚠️ **{message.from_user.mention}**, আপনি আমাদের চ্যানেলে যুক্ত না হওয়া পর্যন্ত এই গ্রুপে মেসেজ পাঠাতে পারবেন না!",
            reply_markup=markup
        )
        await asyncio.sleep(10)
        try:
            await warn_msg.delete()
        except:
            pass
    except Exception as e:
        print(f"Error: {e}")

@Client.on_message(filters.command("broadcast") & filters.user(Config.SUDO_USERS))
async def safe_broadcast(bot: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ যেকোনো মেসেজের রিপ্লাইয়ে `/broadcast user` অথবা `/broadcast group` লিখুন।")

    target = message.command[1] if len(message.command) > 1 else "user"
    if target not in ["user", "group"]:
        return await message.reply_text("⚠️ ব্যবহার পদ্ধতি: `/broadcast user` অথবা `/broadcast group`")

    targets = await get_chats_by_type(target)
    sent, failed = 0, 0
    status = await message.reply_text(f"📢 **{target.capitalize()}** ব্রডকাস্ট শুরু হয়েছে...")

    for cid in targets:
        try:
            await message.reply_to_message.copy(cid)
            sent += 1
            await asyncio.sleep(0.1)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            await message.reply_to_message.copy(cid)
            sent += 1
        except (InputUserDeactivated, UserIsBlocked, ChatAdminRequired):
            failed += 1
        except Exception:
            failed += 1

    await status.edit_text(f"✅ **ব্রডকাস্ট সম্পন্ন!**\n\nগন্তব্য: {target}\nসফল: {sent}\nব্যর্থ: {failed}")
