from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

mongo_client = AsyncIOMotorClient(Config.MONGO_DB_URI)
db = mongo_client["ForceSubscribeBot"]

fsub_collection = db["force_subscribe"]
chats_collection = db["bot_chats"]
security_collection = db["security_settings"]  # 🆕 নতুন সিকিউরিটি কালেকশন

async def add_chat(chat_id: int, chat_type: str):
    await chats_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_type": chat_type}},
        upsert=True
    )

async def get_chats_by_type(chat_type: str):
    cursor = chats_collection.find({"chat_type": chat_type})
    chats = await cursor.to_list(length=None)
    return [c["chat_id"] for c in chats]

async def add_channel(chat_id: int, channel: str):
    await fsub_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"channel": channel}},
        upsert=True
    )

async def get_channel(chat_id: int):
    result = await fsub_collection.find_one({"chat_id": chat_id})
    return result["channel"] if result else None

async def dischannel(chat_id: int):
    await fsub_collection.delete_one({"chat_id": chat_id})


# ==========================================
# 🆕 1. Security Settings DB Logic (Default OFF)
# ==========================================

async def get_security_settings(chat_id: int):
    """গ্রুপের সিকিউরিটি সেটিংস ডাটাবেজ থেকে নিয়ে আসবে।
    ডাটাবেজে ডেটা না থাকলে বাই-ডিফল্ট সবগুলো OFF (False) থাকবে।"""
    result = await security_collection.find_one({"chat_id": chat_id})
    if not result:
        return {
            "link_protection": False,
            "forward_protection": False,
            "username_protection": False
        }
    return result

async def update_security_settings(chat_id: int, setting_key: str, status: bool):
    """গ্রুপ অ্যাডমিন কমান্ড দিলে (on/off) সেটি ডাটাবেজে আপডেট করবে।"""
    await security_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {setting_key: status}},
        upsert=True
    )
