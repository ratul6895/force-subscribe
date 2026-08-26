import re
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatMemberStatus
from database.db import db

# ইউআরএল এবং ইউজারনেম ফিল্টার রেগেক্স (Regex) Pattern
URL_PATTERN = re.compile(r"(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,})")
USERNAME_PATTERN = re.compile(r"@[a-zA-Z0-9_]{3,}")

async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    """মেম্বার অ্যাডমিন বা ওনার কিনা যাচাই করার ইউটিলিটি ফাংশন"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

# ------------------ ANTI-LINK COMMAND ------------------ #
@Client.on_message(filters.command("antilink") & filters.group)
async def antilink_command(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ <b>শুধুমাত্র গ্রুপের অ্যাডমিনগণ এই কমান্ডটি ব্যবহার করতে পারবেন!</b>")
    
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ["on", "off"]:
        return await message.reply_text("💡 <b>সঠিক ব্যবহার:</b>\n• <code>/antilink on</code> — লিঙ্ক পাঠানো ব্লক করতে\n• <code>/antilink off</code> — লিঙ্ক এলাউ করতে")
    
    status = True if args[1].lower() == "on" else False
    await db.set_security_setting(message.chat.id, "antilink", status)
    
    state_txt = "✅ <b>চালু (ON)</b>" if status else "❌ <b>বন্ধ (OFF)</b>"
    await message.reply_text(f"🔗 <b>অ্যান্টি-লিঙ্ক সিকিউরিটি এখন {state_txt} করা হয়েছে!</b>")

# ------------------ ANTI-FORWARD COMMAND ------------------ #
@Client.on_message(filters.command("antiforward") & filters.group)
async def antiforward_command(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ <b>শুধুমাত্র গ্রুপের অ্যাডমিনগণ এই কমান্ডটি ব্যবহার করতে পারবেন!</b>")
    
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ["on", "off"]:
        return await message.reply_text("💡 <b>সঠিক ব্যবহার:</b>\n• <code>/antiforward on</code> — ফরওয়ার্ড মেসেজ ব্লক করতে\n• <code>/antiforward off</code> — ফরওয়ার্ড মেসেজ এলাউ করতে")
    
    status = True if args[1].lower() == "on" else False
    await db.set_security_setting(message.chat.id, "antiforward", status)
    
    state_txt = "✅ <b>চালু (ON)</b>" if status else "❌ <b>বন্ধ (OFF)</b>"
    await message.reply_text(f"↩️ <b>অ্যান্টি-ফরওয়ার্ড সিকিউরিটি এখন {state_txt} করা হয়েছে!</b>")

# ------------------ ANTI-USERNAME COMMAND ------------------ #
@Client.on_message(filters.command("antiusername") & filters.group)
async def antiusername_command(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ <b>শুধুমাত্র গ্রুপের অ্যাডমিনগণ এই কমান্ডটি ব্যবহার করতে পারবেন!</b>")
    
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ["on", "off"]:
        return await message.reply_text("💡 <b>সঠিক ব্যবহার:</b>\n• <code>/antiusername on</code> — ইউজারনেম ট্যাগ ব্লক করতে\n• <code>/antiusername off</code> — ইউজারনেম এলাউ করতে")
    
    status = True if args[1].lower() == "on" else False
    await db.set_security_setting(message.chat.id, "antiusername", status)
    
    state_txt = "✅ <b>চালু (ON)</b>" if status else "❌ <b>বন্ধ (OFF)</b>"
    await message.reply_text(f"🏷️ <b>অ্যান্টি-ইউজারনেম সিকিউরিটি এখন {state_txt} করা হয়েছে!</b>")

# ------------------ SECURITY STATUS COMMAND ------------------ #
@Client.on_message(filters.command(["secstatus", "security"]) & filters.group)
async def secstatus_command(client: Client, message: Message):
    settings = await db.get_security_settings(message.chat.id)
    
    antilink_status = "✅ चालू" if settings.get("antilink") else "❌ বন্ধ"
    antiforward_status = "✅ চালু" if settings.get("antiforward") else "❌ বন্ধ"
    antiusername_status = "✅ चालू" if settings.get("antiusername") else "❌ বন্ধ"
    
    msg = f"""
🛡️ <b>গ্রুপ সিকিউরিটি স্ট্যাটাস (Security Status)</b>

📊 <b>বর্তমান সক্রিয় ফিল্টারসমূহ:</b>
• 🔗 <b>অ্যান্টি-লিঙ্ক (Anti-Link):</b> {antilink_status}
• ↩️ <b>অ্যান্টি-ফরওয়ার্ড (Anti-Forward):</b> {antiforward_status}
• 🏷️ <b>অ্যান্টি-ইউজারনেম (Anti-Username):</b> {antiusername_status}

💡 <i>অ্যাডমিনগণ কমান্ড ব্যবহার করে এই ফিচারগুলো পরিবর্তন করতে পারবেন।</i>
"""
    await message.reply_text(msg)

# ------------------ SPAM FILTER HANDLER ------------------ #
@Client.on_message(filters.group & ~filters.service, group=1)
async def security_filter_handler(client: Client, message: Message):
    if not message.from_user or message.from_user.is_bot:
        return
    
    # অ্যাডমিন বা ওনারদের জন্য সিকিউরিটি নিয়ম প্রযোজ্য নয়
    if await is_admin(client, message.chat.id, message.from_user.id):
        return
        
    settings = await db.get_security_settings(message.chat.id)
    violation_reason = None
    
    text = message.text or message.caption or ""
    
    # ১. অ্যান্টি-লিঙ্ক চেক
    if settings.get("antilink") and URL_PATTERN.search(text):
        violation_reason = "গ্রুপে কোনো ধরণের লিঙ্ক বা URL পোস্ট করা নিষিদ্ধ!"
        
    # ২. অ্যান্টি-ফরওয়ার্ড চেক
    elif settings.get("antiforward") and message.forward_date:
        violation_reason = "অন্য চ্যানেল বা গ্রুপ থেকে মেসেজ ফরওয়ার্ড করা নিষিদ্ধ!"
        
    # ৩. অ্যান্টি-ইউজারনেম চেক
    elif settings.get("antiusername") and USERNAME_PATTERN.search(text):
        violation_reason = "মেসেজে অন্য কারো ইউজারনেম (@username) ট্যাগ করা নিষিদ্ধ!"
        
    if violation_reason:
        try:
            await message.delete()
        except Exception:
            pass
            
        warn_count = await db.add_warning(message.chat.id, message.from_user.id)
        user_mention = message.from_user.mention
        
        if warn_count >= 3:
            # ৩ বার নিয়ম ভাঙলে ২৪ ঘণ্টার জন্য মিউট
            try:
                until_time = datetime.now() + timedelta(days=1)
                await client.restrict_chat_member(
                    message.chat.id,
                    message.from_user.id,
                    ChatPermissions(can_send_messages=False),
                    until_date=until_time
                )
                await db.reset_warnings(message.chat.id, message.from_user.id)
                await client.send_message(
                    message.chat.id,
                    f"🚫 {user_mention} পর পর ৩ বার নিয়ম ভাঙায় আপনাকে <b>২৪ ঘণ্টার জন্য মিউট</b> করা হলো!"
                )
            except Exception as e:
                await client.send_message(message.chat.id, f"⚠️ {user_mention}-কে মিউট করতে সমস্যা হয়েছে। বটকে পর্যাপ্ত অ্যাডমিন পারমিশন দিন।")
        else:
            await client.send_message(
                message.chat.id,
                f"⚠️ {user_mention}, {violation_reason}\n\n🚨 <b>সতর্কবার্তা:</b> [{warn_count}/3] (৩টি সতর্কবার্তা পূর্ণ হলে ২৪ ঘণ্টার জন্য মিউট করা হবে)"
            )
