import motor.motor_asyncio
from config import Config

class Database:
    def __init__(self, uri):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client["ForceSubscribeBot"]
        self.users = self.db["users"]
        self.groups = self.db["groups"]
        self.fsub = self.db["fsub"]
        self.security = self.db["security"]
        self.warnings = self.db["warnings"]

    # ------------------ USER MANAGEMENT ------------------ #
    async def add_user(self, user_id: int, name: str):
        """নতুন ইউজার ডাটাবেজে যুক্ত করে"""
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            await self.users.insert_one({"user_id": user_id, "name": name})

    async def is_user_exist(self, user_id: int) -> bool:
        """ইউজার ডাটাবেজে আছে কিনা চেক করে"""
        user = await self.users.find_one({"user_id": user_id})
        return bool(user)

    async def get_all_users(self):
        """সব ইউজারের তালিকা রিটার্ন করে"""
        return self.users.find({})

    async def total_users_count(self) -> int:
        """মোট প্রাইভেট ইউজার সংখ্যা গণনা করে"""
        return await self.users.count_documents({})

    # ------------------ GROUP MANAGEMENT ------------------ #
    async def add_group(self, chat_id: int, title: str):
        """নতুন গ্রুপ ডাটাবেজে যুক্ত করে"""
        group = await self.groups.find_one({"chat_id": chat_id})
        if not group:
            await self.groups.insert_one({"chat_id": chat_id, "title": title})

    async def get_all_groups(self):
        """সব গ্রুপের তালিকা রিটার্ন করে"""
        return self.groups.find({})

    async def total_groups_count(self) -> int:
        """মোট যুক্ত থাকা গ্রুপের সংখ্যা গণনা করে"""
        return await self.groups.count_documents({})

    # ------------------ FSUB MANAGEMENT ------------------ #
    async def set_fsub(self, chat_id: int, channel: str):
        """গ্রুপের ফোর্স সাবস্ক্রাইব চ্যানেল সেট করে"""
        await self.fsub.update_one(
            {"chat_id": chat_id},
            {"$set": {"channel": channel}},
            upsert=True
        )

    async def get_fsub(self, chat_id: int):
        """গ্রুপের ফোর্স সাবস্ক্রাইব চ্যানেল তথ্য নিয়ে আসে"""
        res = await self.fsub.find_one({"chat_id": chat_id})
        return res["channel"] if res else None

    async def del_fsub(self, chat_id: int):
        """গ্রুপের ফোর্স সাবস্ক্রাইব চ্যানেল মুছে দেয়"""
        await self.fsub.delete_one({"chat_id": chat_id})

    # ------------------ SECURITY SETTINGS ------------------ #
    async def get_security_settings(self, chat_id: int) -> dict:
        """গ্রুপের বর্তমান সিকিউরিটি সেটিংস রিটার্ন করে"""
        res = await self.security.find_one({"chat_id": chat_id})
        if not res:
            default_settings = {
                "chat_id": chat_id,
                "antilink": False,
                "antiforward": False,
                "antiusername": False
            }
            await self.security.insert_one(default_settings)
            return default_settings
        return res

    async def set_security_setting(self, chat_id: int, key: str, value: bool):
        """গ্রুপের কোনো সুনির্দিষ্ট সিকিউরিটি ফিল্টার অন/অফ করে"""
        await self.security.update_one(
            {"chat_id": chat_id},
            {"$set": {key: value}},
            upsert=True
        )

    # ------------------ WARNINGS MANAGEMENT ------------------ #
    async def get_warnings(self, chat_id: int, user_id: int) -> int:
        """ইউজারের বর্তমান ওয়ার্নিং সংখ্যা নিয়ে আসে"""
        res = await self.warnings.find_one({"chat_id": chat_id, "user_id": user_id})
        return res["count"] if res else 0

    async def add_warning(self, chat_id: int, user_id: int) -> int:
        """ইউজারের ওয়ার্নিং ১টি বৃদ্ধি করে এবং নতুন সংখ্যা রিটার্ন করে"""
        res = await self.warnings.find_one({"chat_id": chat_id, "user_id": user_id})
        if res:
            new_count = res["count"] + 1
            await self.warnings.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$set": {"count": new_count}}
            )
            return new_count
        else:
            await self.warnings.insert_one({"chat_id": chat_id, "user_id": user_id, "count": 1})
            return 1

    async def reset_warnings(self, chat_id: int, user_id: int):
        """ইউজারের সব ওয়ার্নিং রিসেট/মুছে দেয়"""
        await self.warnings.delete_one({"chat_id": chat_id, "user_id": user_id})


# ডাটাবেজ ইনস্ট্যান্স অবজেক্ট
db = Database(Config.MONGO_DB_URI)
