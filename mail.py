import telebot, json, os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask
from threading import Thread

# --- তোমার সেটিংস ---
BOT_TOKEN = "8984459858:AAGp4YVV91muymq0ErICTulevJ-ZSsT31ds"
ADMIN_ID = 7952385899
ADMIN_USERNAME = "@AdminUsername"
CHANNEL_LINK = "https://t.me/any_mail_service_bot"
WEBSITE_URL = "https://inspiring-cobbler-5c66bb.netlify.app"

bot = telebot.TeleBot(BOT_TOKEN)

# --- 24 ঘণ্টা জাগিয়ে রাখার জন্য ওয়েব সার্ভার ---
app = Flask('')

@app.route('/')
def home():
    return "MAIL SHOP BD Bot is Alive! 👑"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ডাটাবেস ---
DB_FILE = "users.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f: json.dump({}, f)

def get_users():
    with open(DB_FILE, "r") as f: return json.load(f)
def save_users(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=2)
def get_balance(user_id):
    users = get_users()
    return users.get(str(user_id), {}).get("balance", 0)
def add_balance(user_id, amount):
    users = get_users()
    uid = str(user_id)
    if uid not in users: users[uid] = {"balance": 0, "orders": 0}
    users[uid]["balance"] += amount
    save_users(users)

# --- মেইন মেনু বাটন ---
def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔐  2FA CODE GENERATOR  🔐", web_app=WebAppInfo(url=WEBSITE_URL))
    )
    markup.add(
        InlineKeyboardButton("🛒  MAIL কিনুন", callback_data="buy"),
        InlineKeyboardButton("💎  PREMIUM MAIL", callback_data="premium")
    )
    markup.add(
        InlineKeyboardButton("💰  ব্যালেন্স চেক", callback_data="balance"),
        InlineKeyboardButton("📦  আমার অর্ডার", callback_data="orders")
    )
    markup.add(
        InlineKeyboardButton("💳  টাকা অ্যাড করুন", callback_data="add_money"),
        InlineKeyboardButton("🎁  রেফার করে আয়", callback_data="refer")
    )
    markup.add(
        InlineKeyboardButton("📞  সাপোর্ট", callback_data="support"),
        InlineKeyboardButton("📢  চ্যানেল জয়েন", url=CHANNEL_LINK)
    )
    markup.add(
        InlineKeyboardButton("⭐  রিভিউ দিন", callback_data="review"),
        InlineKeyboardButton("❓  হেল্প", callback_data="help")
    )
    return markup

# --- /start + ব্যানার সহ ---
@bot.message_handler(commands=['start'])
def start(message):
    name = message.from_user.first_name
    uid = str(message.chat.id)
    users = get_users()
    if uid not in users:
        users[uid] = {"balance": 0, "orders": 0, "name": name}
        save_users(users)

    text = (
        f"✨ ━━━━━━━━━━━━━━━ ✨\n"
        f"   👑  𝐌𝐀𝐈𝐋 𝐒𝐇𝐎𝐏 𝐁𝐃  👑\n"
        f"✨ ━━━━━━━━━━━━━━━ ✨\n\n"
        f"👋 হ্যালো, *{name}* !\n"
        f"বাংলাদেশের সবচেয়ে ট্রাস্টেড Mail Shop-এ স্বাগতম। 🇧🇩\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 আপনার আইডি: `{message.chat.id}`\n"
        f"💰 ব্যালেন্স: *{get_balance(message.chat.id)} ৳*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔐 *2FA Code* - ইনস্ট্যান্ট কোড বের করুন\n"
        f"🛒 *Fresh Mail* - 100% Working Guaranteed\n"
        f"⚡ *Instant Delivery* - পেমেন্টের সাথেই ডেলিভারি\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"👇 নিচ থেকে অপশন সিলেক্ট করুন 👇"
    )

    try:
        with open("banner.jpg", "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=text, parse_mode="Markdown", reply_markup=main_menu())
    except:
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(commands=['balance'])
def balance_cmd(message):
    bot.send_message(message.chat.id, f"💰 আপনার ব্যালেন্স: *{get_balance(message.chat.id)} ৳*", parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, "❓ হেল্প লাগলে মেসেজ দিন: " + ADMIN_USERNAME)

# --- সব বাটনের কাজ ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    cid = call.message.chat.id
    data = call.data

    if data == "buy":
        bot.answer_callback_query(call.id)
        m = InlineKeyboardMarkup(row_width=2)
        m.add(
            InlineKeyboardButton("📧 Gmail - 30৳", callback_data="buy_gmail"),
            InlineKeyboardButton("📧 Outlook - 25৳", callback_data="buy_outlook"),
            InlineKeyboardButton("📧 Yahoo - 20৳", callback_data="buy_yahoo"),
            InlineKeyboardButton("🔙 Back", callback_data="back_home")
        )
        bot.send_message(cid, "🛒 *কোন Mail কিনবেন সিলেক্ট করুন:*", parse_mode="Markdown", reply_markup=m)

    elif data.startswith("buy_"):
        bot.answer_callback_query(call.id)
        item = data.replace("buy_", "").upper()
        bot.send_message(cid, f"🛒 আপনি *{item}* সিলেক্ট করেছেন।\n\nঅর্ডার করতে এডমিনকে মেসেজ দিন: {ADMIN_USERNAME}", parse_mode="Markdown")

    elif data == "premium":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, "💎 *PREMIUM MAIL*\n\n✅ Old / Aged Mail\n✅ High Quality\n✅ Full Access\n\nঅর্ডার করতে: " + ADMIN_USERNAME, parse_mode="Markdown")

    elif data == "balance":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, f"💰 *আপনার ব্যালেন্স:* `{get_balance(cid)} ৳`\n\nটপ-আপ করতে নিচে টাকা অ্যাড করুন বাটনে চাপ দিন।", parse_mode="Markdown")

    elif data == "orders":
        bot.answer_callback_query(call.id)
        users = get_users()
        orders = users.get(str(cid), {}).get("orders", 0)
        bot.send_message(cid, f"📦 *আপনার মোট অর্ডার:* {orders} টি\n\nকোনো অর্ডার না থাকলে Buy থেকে কিনুন।", parse_mode="Markdown")

    elif data == "add_money":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, f"💳 *টাকা অ্যাড করুন:*\n\n1. বিকাশ / নগদে টাকা পাঠান\n2. TrxID সহ এডমিনকে মেসেজ দিন: {ADMIN_USERNAME}\n\n✅ 5 মিনিটের ভিতর ব্যালেন্স অ্যাড হয়ে যাবে।", parse_mode="Markdown")

    elif data == "refer":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, f"🎁 *রেফার করে আয় করুন!*\n\nআপনার লিংক:\n`https://t.me/YourBotUsername?start={cid}`\n\nপ্রতি রেফারে 10৳ বোনাস!", parse_mode="Markdown")

    elif data == "support":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, f"📞 *সাপোর্ট:*\n{ADMIN_USERNAME}\n\n⏰ Reply Time: 5-10 মিনিট", parse_mode="Markdown")

    elif data == "review":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, f"⭐ ধন্যবাদ! আমাদের চ্যানেলে রিভিউ দিন:\n{CHANNEL_LINK}")

    elif data == "help":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, "❓ *হেল্প:*\n\n🔐 2FA - কোড বের করতে 2FA বাটনে চাপ দিন\n🛒 Mail কিনতে - Mail কিনুন বাটনে চাপ দিন\n💰 ব্যালেন্স - ব্যালেন্স দেখতে ব্যালেন্স বাটনে চাপ দিন\n\nআরো হেল্প লাগলে: " + ADMIN_USERNAME, parse_mode="Markdown")

    elif data == "back_home":
        bot.answer_callback_query(call.id)
        bot.send_message(cid, "🏠 হোম মেনু:", reply_markup=main_menu())

# --- এডমিন কমান্ড ---
@bot.message_handler(commands=['add'])
def add_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, uid, amount = message.text.split()
        add_balance(int(uid), int(amount))
        bot.send_message(message.chat.id, f"✅ {uid} কে {amount}৳ দেওয়া হয়েছে।")
        bot.send_message(int(uid), f"✅ আপনার অ্যাকাউন্টে *{amount}৳* অ্যাড হয়েছে!\nনতুন ব্যালেন্স: {get_balance(int(uid))}৳", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "ব্যবহার: /add <user_id> <amount>")

keep_alive()
print("Bot Running...")
bot.infinity_polling()
