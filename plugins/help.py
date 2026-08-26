from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import Messages

def get_help_buttons(current_page: int):
    """হেল্প মেনুর পেজিনেশন ইনলাইন বাটন জেনারেট করে"""
    buttons = []
    
    # নেভিগেশন বাটন (Previous / Next)
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ পূর্ববর্তী", callback_data=f"help_page_{current_page - 1}"))
    if current_page < 4:
        nav_buttons.append(InlineKeyboardButton("পরবর্তী ➡️", callback_data=f"help_page_{current_page + 1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
        
    # মেনু ক্লোজ বাটন
    buttons.append([InlineKeyboardButton("❌ মেনু বন্ধ করুন", callback_data="close_help")])
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    """ইউজার প্রাইভেটে /help দিলে প্রথম পেজ দেখায়"""
    await message.reply_text(
        text=Messages.HELP_MSG[1],
        reply_markup=get_help_buttons(1),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r"^help_page_(\d+)$"))
async def help_page_callback(client: Client, query: CallbackQuery):
    """ইনলাইন বাটন ক্লিক করলে পৃষ্ঠা পরিবর্তন করে"""
    page = int(query.data.split("_")[-1])
    
    if page in Messages.HELP_MSG:
        await query.message.edit_text(
            text=Messages.HELP_MSG[page],
            reply_markup=get_help_buttons(page),
            disable_web_page_preview=True
        )
        await query.answer()
    else:
        await query.answer("❌ কোনো পৃষ্ঠা পাওয়া যায়নি!", show_alert=True)

@Client.on_callback_query(filters.regex("^close_help$"))
async def close_help_callback(client: Client, query: CallbackQuery):
    """হেল্প মেনু ডিলিট করার বাটন"""
    await query.message.delete()
    await query.answer("মেনু বন্ধ করা হয়েছে।")
