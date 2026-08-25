from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

mongo_client = AsyncIOMotorClient(Config.MONGO_DB_URI)
db = mongo_client["ForceSubscribeBot"]

fsub_collection = db["force_subscribe"]
chats_collection = db["bot_chats"]

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
