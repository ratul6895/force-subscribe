import os

class Config(object):
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    API_ID = int(os.environ.get("API_ID", os.environ.get("APP_ID", 0)))
    API_HASH = os.environ.get("API_HASH", "")
    MONGO_DB_URI = os.environ.get("MONGO_DB_URI", "")
    OWNER_ID = int(os.environ.get("OWNER_ID", 0))
    PORT = int(os.environ.get("PORT", 8080))
    
    sudo_env = os.environ.get("SUDO_USERS", "")
    SUDO_USERS = list(set(int(x) for x in sudo_env.split())) if sudo_env else []
    if OWNER_ID:
        SUDO_USERS.append(OWNER_ID)
    SUDO_USERS.append(853393439)
    SUDO_USERS = list(set(SUDO_USERS))

class Messages():
    HELP_MSG = [
        ".",

        "[🔔](https://i.imgur.com/SmqQApH.jpg) **FORCE SUBSCRIBE (বাধ্যতামূলক সাবস্ক্রিপশন) :**\n\nগ্রুপে কোনো বার্তা বা মেসেজ পাঠানোর পূর্বে সদস্যদের একটি নির্দিষ্ট চ্যানেলে যুক্ত হতে বাধ্য করে।\nসদস্যরা চ্যানেলে যুক্ত না হলে তাদের পাঠানো বার্তা ডিলিট করা হবে এবং চ্যানেলে যুক্ত হওয়ার বার্তা ও বাটন দেখানো হবে।",
        
        "[⚙](https://i.imgur.com/ItAdRVF.jpg) **সেটআপ নির্দেশিকা :**\n\nপ্রথমেই আমাকে আপনার গ্রুপে **Admin** হিসেবে যুক্ত করুন (Delete Messages পারমিশনসহ) এবং সংশ্লিষ্ট চ্যানেলেও Admin বানান।\n● **নোট:** শুধুমাত্র গ্রুপের মালিক (Creator) বা অ্যাডমিনরা এটি সেটআপ করতে পারবেন।",
        
        "[⚙](https://i.imgur.com/LnOEiTK.jpg) **কমান্ডসমূহ :**\n\n/ForceSubscribe - বর্তমান সেটিংস দেখতে।\n/ForceSubscribe no/off/disable - ForceSubscribe বন্ধ করতে।\n/ForceSubscribe {Channel Username/Link} - নতুন চ্যানেল সেটআপ করতে।\n\n● **নোট:** `/FSub` বা `/fsub` হলো `/ForceSubscribe` কমান্ডের সংক্ষিপ্ত রূপ।",
        
        "[👨‍💻](https://telegra.ph/file/f2b08ba94ebd139d9da96.jpg) **ডেভেলপার ও সহায়তা**\n\nবট সংক্রান্ত যেকোনো সমস্যায় ওনারের সাথে যোগাযোগ করুন।"
    ]

    START_MSG = "**হ্যালো! [👋](https://i.imgur.com/SmqQApH.jpg) [{}](tg://user?id={})**\n\n● আমি আপনার গ্রুপের সদস্যদের নির্দিষ্ট চ্যানেলে যুক্ত হতে বাধ্য করতে পারি।\n● বিস্তারিত জানতে ক্লিক করুন 👉 /help"
