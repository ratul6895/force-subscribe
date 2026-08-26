from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, PeerIdInvalid
from database.db import db

async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    """ইউজার গ্রুপের অ্যাডমিন বা ওনার কিনা চেক করে"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

# ------------------ FSUB SET COMMAND ------------------ #
@Client.on_message(filters.command("fsub") & filters.group)
async def fsub_command(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ <b>শুধুমাত্র গ্রুপের অ্যাডমিনগণ এই কমান্ডটি ব্যবহার করতে পারবেন!</b>")

    args = message.text.split()

    # ১. বর্তমান FSub স্ট্যাটাস দেখা
    if len(args) == 1:
        channel = await db.get_fsub(message.chat.id)
        if channel:
            return await message.reply_text(f"📢 <b>বর্তমান ফোর্স সাবস্ক্রাইব চ্যানেল:</b> @{channel}\n\n💡 বন্ধ করতে টাইপ করুন: <code>/fsub off</code>")
        else:
            return await message.reply_text("❌ <b>এই গ্রুপে বর্তমানে কোনো ফোর্স সাবস্ক্রাইব চ্যানেল যুক্ত নেই!</b>\n\n💡 চ্যানেল যুক্ত করতে টাইপ করুন: <code>/fsub @YourChannel</code>")

    input_channel = args[1].strip()

    # ২. FSub অফ করা
    if input_channel.lower() == "off":
        await db.del_fsub(message.chat.id)
        return await message.reply_text("✅ <b>ফোর্স সাবস্ক্রাইব সফলভাবে বন্ধ করা হয়েছে!</b>")

    # ৩. চ্যানেল ইউজারনেম ফিল্টারিং ও ভ্যালিডেশন
    clean_channel = input_channel.replace("https://t.me/", "").replace("http://t.me/", "").replace("@", "").split("/")[0]

    try:
        chat_member = await client.get_chat_member(f"@{clean_channel}", "me")
        if chat_member.status != ChatMemberStatus.ADMINISTRATOR:
            return await message.reply_text(f"⚠️ <b>বটটি @{clean_channel} চ্যানেলে অ্যাডমিন নয়!</b>\n\nঅনুগ্রহ করে প্রথমে বটকে ওই চ্যানেলে অ্যাডমিন বানান।")
    except Exception as e:
        return await message.reply_text(f"❌ <b>চ্যানেল যাচাই করতে ব্যর্থ হয়েছে!</b>\n\nইনপুট করা ইউজারনেম সঠিক কিনা চেক করুন: <code>@{clean_channel}</code>")

    # ডাটাবেজে সেভ
    await db.set_fsub(message.chat.id, clean_channel)
    await message.reply_text(f"🎉 <b>সফলভাবে ফোর্স সাবস্ক্রাইব চ্যানেল সেট করা হয়েছে!</b>\n\n📢 <b>চ্যানেল:</b> @{clean_channel}")


# ------------------ FSUB CHECKER HANDLER ------------------ #
@Client.on_message(filters.group & ~filters.service, group=2)
async def fsub_message_handler(client: Client, message: Message):
    if not message.from_user or message.from_user.is_bot:
        return

    # অ্যাডমিনদের জন্য FSub শিথিলযোগ্য
    if await is_admin(client, message.chat.id, message.from_user.id):
        return

    fsub_channel = await db.get_fsub(message.chat.id)
    if not fsub_channel:
        return

    # ইউজার চ্যানেলে জয়েন আছে কিনা চেক করা
    is_subscribed = False
    try:
        member = await client.get_chat_member(f"@{fsub_channel}", message.from_user.id)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            is_subscribed = True
    except UserNotParticipant:
        is_subscribed = False
    except Exception:
        # চ্যানেল না পাওয়া গেলে বা কোনো ত্রুটি হলে
        return

    if not is_subscribed:
        try:
            await message.delete()
        except Exception:
            pass

        user_mention = message.from_user.mention
        join_link = f"https://t.me/{fsub_channel}"

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 চ্যানেলে জয়েন করুন", url=join_link)],
            [InlineKeyboardButton("🔄 জয়েন করা শেষ (Try Again)", callback_data=f"check_fsub_{fsub_channel}")]
        ])

        warning_msg = (
            f"👋 <b>হে {user_mention},</b>\n\n"
            f"গ্রুপে বার্তা পাঠাতে হলে আপনাকে অবশ্যই আমাদের অফিসিয়াল চ্যানেলে জয়েন করতে হবে।\n\n"
            f"👇 নিচের বাটন থেকে জয়েন করে <b>'Try Again'</b> বাটনে ক্লিক করুন:"
        )

        try:
            await client.send_message(
                chat_id=message.chat.id,
                text=warning_msg,
                reply_markup=buttons
            )
        except Exception:
            pass


# ------------------ TRY AGAIN CALLBACK HANDLER ------------------ #
@Client.on_callback_query(filters.regex(r"^check_fsub_(.+)"))
async def check_fsub_callback(client: Client, query: CallbackQuery):
    channel = query.data.split("_")[-1]
    user_id = query.from_user.id

    try:
        member = await client.get_chat_member(f"@{channel}", user_id)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await query.answer("✅ ধন্যবাদ! আপনি চ্যানেলে জয়েন করেছেন। এখন গ্রুপে মেসেজ দিতে পারবেন।", show_alert=True)
            try:
                await query.message.delete()
            except Exception:
                pass
        else:
            await query.answer("❌ আপনি এখনো চ্যানেলে জয়েন করেননি! অনুগ্রহ করে আগে জয়েন করুন।", show_alert=True)
    except UserNotParticipant:
        await query.answer("❌ আপনি এখনো চ্যানেলে জয়েন করেননি! অনুগ্রহ করে আগে জয়েন করুন।", show_alert=True)
    except Exception:
        await query.answer("⚠️ একটি সমস্যা হয়েছে, আবার চেষ্টা করুন।", show_alert=True)
