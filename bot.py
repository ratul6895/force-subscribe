import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config, Messages
from database.db import db

# ------------------ START COMMAND ------------------ #
@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    # প্রাইভেট মেসেজ হলে ইউজারকে ডাটাবেজে সেভ করা
    if message.chat.type.value == "private":
        await db.add_user(user_id, first_name)
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ বটকে আপনার গ্রুপে যোগ করুন", url=f"https://t.me/{client.me.username}?startgroup=true"),
            ],
            [
                InlineKeyboardButton("📜 সাহায্য ও নির্দেশিকা", callback_data="help_page_1"),
                InlineKeyboardButton("📢 অফিসিয়াল চ্যানেল", url="https://t.me/official_botbox")
            ]
        ])
        
        await message.reply_text(
            text=Messages.START_MSG.format(first_name, user_id),
            reply_markup=buttons,
            disable_web_page_preview=True
        )
    else:
        # গ্রুপে স্টার্ট কমান্ড দিলে
        await db.add_group(message.chat.id, message.chat.title)
        await message.reply_text(
            f"👋 <b>হ্যালো {first_name}!</b>\n\nআমি এই গ্রুপে সক্রিয় আছি। বটের সব কমান্ড এবং ব্যবহারের নির্দেশিকা দেখতে ইনবক্সে /help লিখুন।"
        )


# ------------------ STATS COMMAND (SUDO ONLY) ------------------ #
@Client.on_message(filters.command(["stats", "status"]))
async def stats_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # সুডো ইউজার চেক
    if user_id not in Config.SUDO_USERS:
        return await message.reply_text("❌ <b>শুধুমাত্র বটের ওনার/সুডো ব্যবহারকারীগণ এই কমান্ডটি ব্যবহার করতে পারবেন!</b>")
        
    msg = await message.reply_text("🔄 <i>ডাটাবেজ থেকে স্ট্যাটাস লোড হচ্ছে...</i>")
    
    total_users = await db.total_users_count()
    total_groups = await db.total_groups_count()
    
    stats_text = f"""
📊 <b>বট লাইভ স্ট্যাটিস্টিকস (Live Stats)</b>

👤 <b>মোট প্রাইভেট ইউজার:</b> <code>{total_users}</code>
👥 <b>মোট অ্যাক্টিভ গ্রুপ:</b> <code>{total_groups}</code>
⚡ <b>বট স্ট্যাটাস:</b> সক্রিয় (Online)
"""
    await msg.edit_text(stats_text)


# ------------------ BROADCAST COMMAND (SUDO ONLY) ------------------ #
@Client.on_message(filters.command("broadcast") & filters.reply)
async def broadcast_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in Config.SUDO_USERS:
        return await message.reply_text("❌ <b>শুধুমাত্র বটের ওনার/সুডো ব্যবহারকারীগণ এই কমান্ডটি ব্যবহার করতে পারবেন!</b>")
        
    broadcast_msg = message.reply_to_message
    args = message.text.split()
    
    target = "all"
    if len(args) > 1:
        target = args[1].lower() # 'user', 'group', or 'all'
        
    status_msg = await message.reply_text("🚀 <b>ব্রডকাস্ট প্রক্রিয়া শুরু হচ্ছে...</b>")
    
    sent_users = 0
    failed_users = 0
    sent_groups = 0
    failed_groups = 0
    
    # প্রাইভেট ইউজারদের ব্রডকাস্ট
    if target in ["all", "user"]:
        users = await db.get_all_users()
        async for user in users:
            try:
                await broadcast_msg.copy(chat_id=user["user_id"])
                sent_users += 1
                await asyncio.sleep(0.05) # রেট লিমিট এড়াতে ছোট বিরতি
            except Exception:
                failed_users += 1

    # গ্রুপগুলোতে ব্রডকাস্ট
    if target in ["all", "group"]:
        groups = await db.get_all_groups()
        async for group in groups:
            try:
                await broadcast_msg.copy(chat_id=group["chat_id"])
                sent_groups += 1
                await asyncio.sleep(0.05)
            except Exception:
                failed_groups += 1

    result_text = f"""
📢 <b>ব্রডকাস্ট রিপোর্ট সম্পন্ন!</b>

👤 <b>ইউজারদের ফল:</b>
└ ✅ সফল: <code>{sent_users}</code> | ❌ ব্যর্থ: <code>{failed_users}</code>

👥 <b>গ্রুপের ফল:</b>
└ ✅ সফল: <code>{sent_groups}</code> | ❌ ব্যর্থ: <code>{failed_groups}</code>
"""
    await status_msg.edit_text(result_text)
