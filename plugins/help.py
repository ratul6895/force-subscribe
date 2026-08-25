from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Messages

@Client.on_message(filters.command("help") & filters.private)
async def help_command(bot: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("◀️ পূর্ববর্তী", callback_data="help_prev"),
            InlineKeyboardButton("পরবর্তী ▶️", callback_data="help_next")
        ]
    ])
    await message.reply_text(
        text=Messages.HELP_MSG[1],
        reply_markup=buttons,
        disable_web_page_preview=False
    )

@Client.on_callback_query(filters.regex(r"^help_"))
async def help_button_click(bot: Client, query: CallbackQuery):
    # সাহায্য বার্তা নেভিগেশন হ্যান্ডলার
    current_text = query.message.text or ""
    page = 1
    if "সেটআপ নির্দেশিকা" in query.message.caption or "সেটআপ নির্দেশিকা" in current_text:
        page = 2
    elif "কমান্ডসমূহ" in query.message.caption or "কমান্ডসমূহ" in current_text:
        page = 3
    elif "ডেভেলপার" in query.message.caption or "ডেভেলপার" in current_text:
        page = 4

    if query.data == "help_next":
        page = page + 1 if page < 4 else 1
    else:
        page = page - 1 if page > 1 else 4

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("◀️ পূর্ববর্তী", callback_data="help_prev"),
            InlineKeyboardButton("পরবর্তী ▶️", callback_data="help_next")
        ]
    ])
    
    await query.message.edit_text(
        text=Messages.HELP_MSG[page],
        reply_markup=buttons,
        disable_web_page_preview=False
    )
