import telebot
from telebot import types
import json, os
from openpyxl import Workbook, load_workbook
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home():
    return "MAIL SHOP BD Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
Thread(target=run_web, daemon=True).start()

# টোকেন কোডে রাখবা না, Railway Variables থেকে আসবে
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7952385899
ADMIN_USERNAME = "@DULU_VAI"
bot = telebot.TeleBot(BOT_TOKEN)

DEFAULT_DASH = """╔═══════════════════════╗
║ 💎 MAIL SHOP BD 💎 ║
╚═══════════════════════╝
👤 Name: {name}
💌 Username: {username}
🆔 ID: {uid}
💰 Balance: {bal:.2f} Tk

🛒 নিচ থেকে প্রোডাক্ট সিলেক্ট করে কিনো।"""

def save():
    json.dump(data, open("data.json","w"))

if not os.path.exists("data.json"):
    data = {"products": {}, "users": {}, "payments": {}, "channels": [], "temp": {}, "orders": {}, "settings": {"dashboard": DEFAULT_DASH, "banner": None}}
    json.dump(data, open("data.json","w"))
else:
    try:
        data = json.load(open("data.json"))
    except:
        data = {"products": {}, "users": {}, "payments": {}, "channels": [], "temp": {}, "orders": {}, "settings": {"dashboard": DEFAULT_DASH, "banner": None}}
        save()

if "settings" not in data:
    data["settings"] = {"dashboard": DEFAULT_DASH, "banner": None}
if "temp" not in data:
    data["temp"] = {}
if "orders" not in data:
    data["orders"] = {}
if "users" not in data:
    data["users"] = {}
if "products" not in data:
    data["products"] = {}
if "payments" not in data:
    data["payments"] = {}
if "channels" not in data:
    data["channels"] = []
save()

def get_user(uid, msg=None):
    uid = str(uid)
    if uid not in data["users"]:
        name = msg.from_user.first_name if msg else ""
        username = msg.from_user.username or "" if msg else ""
        data["users"][uid] = {"balance": 0, "name": name, "username": username, "bought": [], "bought_count": 0}
        save()
    else:
        if msg:
            if msg.from_user.first_name:
                data["users"][uid]["name"] = msg.from_user.first_name
            if msg.from_user.username:
                data["users"][uid]["username"] = msg.from_user.username
            save()
    return data["users"][uid]

def is_header_row(row):
    txt = " ".join([str(v).lower() for v in row if v is not None])
    return "email" in txt and "pass" in txt

def count_stock(key):
    path = f"stock_{key}.xlsx"
    if not os.path.exists(path):
        return 0
    try:
        wb = load_workbook(path)
        ws = wb.active
        c = 0
        first = True
        for row in ws.iter_rows(values_only=True):
            if not any(v is not None and str(v).strip() != "" for v in row):
                continue
            if first and is_header_row(row):
                first = False
                continue
            first = False
            c += 1
        return c
    except:
        return 0

def get_stock_rows(key):
    path = f"stock_{key}.xlsx"
    if not os.path.exists(path):
        return None, []
    wb = load_workbook(path)
    ws = wb.active
    rows = []
    first = True
    header = None
    for row in ws.iter_rows(values_only=True):
        if not any(v is not None and str(v).strip() != "" for v in row):
            continue
        if first and is_header_row(row):
            header = list(row)
            first = False
            continue
        first = False
        rows.append(list(row))
    return header, rows

def check_join(uid):
    for ch in data["channels"]:
        try:
            m = bot.get_chat_member(ch, int(uid))
            if m.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

def join_markup():
    markup = types.InlineKeyboardMarkup()
    for ch in data["channels"]:
        markup.add(types.InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch.replace('@','')}"))
    markup.add(types.InlineKeyboardButton("Join করছি, Check করো", callback_data="check_join"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid in data["temp"]:
        del data["temp"][uid]
        save()
    get_user(uid, message)
    if data["channels"] and not check_join(uid):
        bot.send_message(message.chat.id, "আগে চ্যানেলে জয়েন করো!", reply_markup=join_markup())
        return
    show_menu(message.chat.id, uid, message)

@bot.message_handler(commands=['cancel'])
def cancel_cmd(message):
    uid = str(message.from_user.id)
    if uid in data["temp"]:
        del data["temp"][uid]
        save()
        bot.send_message(message.chat.id, "❌ ক্যানসেল হইছে। /start দাও।")
    else:
        bot.send_message(message.chat.id, "ক্যানসেল করার মতো কিছু নাই। /start দাও।")

@bot.message_handler(commands=['myorders'])
def myorders(message):
    uid = str(message.from_user.id)
    u = get_user(uid, message)
    if not u.get("bought"):
        bot.send_message(message.chat.id, "তুমি এখনো কিছু কিনো নাই।")
        return
    txt = "🛒 তোমার অর্ডার:\n\n" + "\n".join([f"• {x}" for x in u["bought"]])
    txt += f"\n\nমোট কিনছো: {u['bought_count']} টা\nব্যালেন্স: {u['balance']} Tk"
    bot.send_message(message.chat.id, txt)

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, "কমান্ড:\n/start - মেনু\n/myorders - আমার কেনাকাটা\n/cancel - চলমান কাজ বাদ দাও")

def show_menu(chat_id, uid, message=None):
    u = get_user(uid, message)
    name = u.get("name") or (message.from_user.first_name if message else "User")
    username = f"@{u.get('username')}" if u.get("username") else "@NoUsername"
    bal = u["balance"]
    dash_template = data["settings"].get("dashboard") or DEFAULT_DASH
    try:
        text = dash_template.format(name=name, username=username, uid=uid, bal=bal)
    except:
        text = dash_template
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(f"💰 Balance: {bal:.2f} Tk", callback_data="mybal"))
    markup.add(types.InlineKeyboardButton("💳 ডিপোজিট করো", callback_data="deposit"))
    markup.add(types.InlineKeyboardButton("🛒 আমার অর্ডার", callback_data="myorders_btn"))
    for key, p in data["products"].items():
        stock = count_stock(key)
        stock_emoji = "✅" if stock > 0 else "❌"
        markup.add(types.InlineKeyboardButton(f"💎 {p['name']} - {p['price']} Tk | {stock_emoji} স্টক: {stock}", callback_data=f"buy_{key}"))
    markup.add(types.InlineKeyboardButton("🚀 START SHOPPING NOW 🚀", callback_data="back_menu"))
    markup.add(types.InlineKeyboardButton(f"💬 Support - {ADMIN_USERNAME}", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}"))
    banner = data["settings"].get("banner")
    if banner and os.path.exists("banner.jpg"):
        try:
            with open("banner.jpg","rb") as f:
                bot.send_photo(chat_id, f, caption=text, reply_markup=markup)
            return
        except:
            pass
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data=="check_join")
def check_join_btn(call):
    uid = str(call.from_user.id)
    if check_join(uid):
        bot.answer_callback_query(call.id, "জয়েন হইছে!")
        bot.send_message(call.message.chat.id, "জয়েন হইছে!")
        show_menu(call.message.chat.id, uid, call)
    else:
        bot.answer_callback_query(call.id, "এখনো জয়েন করো নাই!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data=="mybal")
def mybal(call):
    u = get_user(call.from_user.id)
    bot.answer_callback_query(call.id, f"তোমার ব্যালেন্স: {u['balance']} Tk", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data=="myorders_btn")
def myorders_btn(call):
    bot.answer_callback_query(call.id)
    uid = str(call.from_user.id)
    u = get_user(uid, call)
    if not u.get("bought"):
        bot.send_message(call.message.chat.id, "তুমি এখনো কিছু কিনো নাই।")
        return
    txt = "🛒 তোমার অর্ডার:\n\n" + "\n".join([f"• {x}" for x in u["bought"]])
    bot.send_message(call.message.chat.id, txt)

@bot.callback_query_handler(func=lambda c: c.data=="back_menu")
def back_menu(call):
    bot.answer_callback_query(call.id)
    show_menu(call.message.chat.id, str(call.from_user.id), call)

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("✏️ ড্যাশবোর্ড মেসেজ চেঞ্জ", callback_data="admin_change_dash"))
    markup.add(types.InlineKeyboardButton("🖼️ ব্যানার চেঞ্জ", callback_data="admin_change_banner"))
    markup.add(types.InlineKeyboardButton("➕ প্রোডাক্ট Add", callback_data="admin_add_product"))
    markup.add(types.InlineKeyboardButton("🗑️ প্রোডাক্ট Delete", callback_data="admin_del_list"))
    markup.add(types.InlineKeyboardButton("📤 Excel Upload / স্টক Add", callback_data="admin_upload_list"))
    markup.add(types.InlineKeyboardButton("📢 সবাইকে মেসেজ (Broadcast)", callback_data="broadcast_start"))
    markup.add(types.InlineKeyboardButton("📊 Status", callback_data="status"))
    markup.add(types.InlineKeyboardButton("📥 Receive - Excel", callback_data="receive_excel"))
    markup.add(types.InlineKeyboardButton("📋 চ্যানেল লিস্ট", callback_data="channel_list"))
    bot.send_message(message.chat.id, f"👑 এডমিন প্যানেল\n\nপেমেন্ট: /addpayment bkash 016XXX\nচ্যানেল: /addchannel @mychannel\nব্যালেন্স দিতে: /addbalance আইডি টাকা\nব্যালেন্স কাটতে: /removebalance আইডি টাকা", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data=="channel_list")
def channel_list(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    if not data["channels"]:
        bot.send_message(call.message.chat.id, "কোনো চ্যানেল নাই।")
        return
    bot.send_message(call.message.chat.id, "চ্যানেল লিস্ট:\n" + "\n".join(data["channels"]) + "\n\nডিলিট করতে: /delchannel @name")

@bot.message_handler(commands=['addbalance'])
def addbalance(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, uid, amt = message.text.split()
        amt = int(amt)
        get_user(uid)
        data["users"][uid]["balance"] += amt
        save()
        bot.send_message(message.chat.id, f"✅ {uid} কে {amt} Tk দেওয়া হইছে। নতুন ব্যালেন্স: {data['users'][uid]['balance']} Tk")
        try:
            bot.send_message(int(uid), f"✅ এডমিন তোমাকে {amt} Tk দিছে। নতুন ব্যালেন্স: {data['users'][uid]['balance']} Tk")
        except:
            pass
    except:
        bot.send_message(message.chat.id, "ভুল! /addbalance আইডি টাকা")

@bot.message_handler(commands=['removebalance'])
def removebalance(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, uid, amt = message.text.split()
        amt = int(amt)
        get_user(uid)
        data["users"][uid]["balance"] -= amt
        save()
        bot.send_message(message.chat.id, f"✅ {uid} থেকে {amt} Tk কাটা হইছে।")
    except:
        bot.send_message(message.chat.id, "ভুল! /removebalance আইডি টাকা")

@bot.callback_query_handler(func=lambda c: c.data=="admin_change_dash")
def change_dash_start(call):
    if call.from_user.id != ADMIN_ID:
        return
    data["temp"][str(call.from_user.id)] = {"step": "change_dash"}
    save()
    bot.send_message(call.message.chat.id, "নতুন ড্যাশবোর্ড মেসেজ লিখে পাঠাও।\n{name} {username} {uid} {bal} ব্যবহার করতে পারবা।")

@bot.message_handler(func=lambda m: str(m.from_user.id) in data["temp"] and data["temp"][str(m.from_user.id)].get("step")=="change_dash")
def change_dash_save(message):
    if message.from_user.id != ADMIN_ID:
        return
    data["settings"]["dashboard"] = message.text
    del data["temp"][str(message.from_user.id)]
    save()
    bot.send_message(message.chat.id, "✅ ড্যাশবোর্ড চেঞ্জ হইছে!")

@bot.callback_query_handler(func=lambda c: c.data=="admin_change_banner")
def change_banner_start(call):
    if call.from_user.id != ADMIN_ID:
        return
    data["temp"][str(call.from_user.id)] = {"step": "change_banner"}
    save()
    bot.send_message(call.message.chat.id, "নতুন ব্যানার ছবিটা পাঠাও।")

@bot.message_handler(commands=['addchannel'])
def addch(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, ch = message.text.split()
        if ch not in data["channels"]:
            data["channels"].append(ch)
            save()
        bot.send_message(message.chat.id, f"চ্যানেল Add: {ch}")
    except:
        bot.send_message(message.chat.id, "ভুল! /addchannel @mychannel")

@bot.message_handler(commands=['delchannel'])
def delch(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, ch = message.text.split()
        data["channels"].remove(ch)
        save()
        bot.send_message(message.chat.id, "চ্যানেল Delete হইছে")
    except:
        bot.send_message(message.chat.id, "ভুল! /delchannel @mychannel")

@bot.message_handler(commands=['addpayment'])
def addpay(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, key, num = message.text.split()
        data["payments"][key.lower()] = num
        save()
        bot.send_message(message.chat.id, f"পেমেন্ট Add: {key} - {num}")
    except:
        bot.send_message(message.chat.id, "ভুল! /addpayment bkash 016XXX")

@bot.message_handler(commands=['delpayment'])
def delpay(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, key = message.text.split()
        del data["payments"][key.lower()]
        save()
        bot.send_message(message.chat.id, "ডিলিট হইছে")
    except:
        bot.send_message(message.chat.id, "ভুল! /delpayment bkash")

@bot.callback_query_handler(func=lambda c: c.data=="admin_add_product")
def admin_add_start(call):
    if call.from_user.id != ADMIN_ID:
        return
    data["temp"][str(call.from_user.id)] = {"step": "prod_name"}
    save()
    bot.send_message(call.message.chat.id, "প্রোডাক্টের নাম কি? ক্যানসেল করতে /cancel")

@bot.message_handler(func=lambda m: str(m.from_user.id) in data["temp"] and data["temp"][str(m.from_user.id)].get("step")=="prod_name")
def prod_name_step(message):
    if message.from_user.id != ADMIN_ID:
        return
    uid = str(message.from_user.id)
    data["temp"][uid]["prod_name"] = message.text.strip()
    data["temp"][uid]["step"] = "prod_price"
    save()
    bot.send_message(message.chat.id, f"নাম: {message.text}\n\nএখন দাম কত? যেমন: 50")

@bot.message_handler(func=lambda m: str(m.from_user.id) in data["temp"] and data["temp"][str(m.from_user.id)].get("step")=="prod_price")
def prod_price_step(message):
    if message.from_user.id != ADMIN_ID:
        return
    uid = str(message.from_user.id)
    try:
        price = int(message.text.strip())
    except:
        bot.send_message(message.chat.id, "শুধু সংখ্যা লিখো। যেমন: 50")
        return
    data["temp"][uid]["prod_price"] = price
    data["temp"][uid]["step"] = "prod_excel"
    save()
    bot.send_message(message.chat.id, f"দাম: {price} Tk / পিস\n\nএখন Excel ফাইলটা পাঠাও।")

@bot.callback_query_handler(func=lambda c: c.data=="admin_upload_list")
def upload_list(call):
    if call.from_user.id != ADMIN_ID:
        return
    if not data["products"]:
        bot.send_message(call.message.chat.id, "কোনো প্রোডাক্ট নাই।")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, p in data["products"].items():
        markup.add(types.InlineKeyboardButton(f"{p['name']} - স্টক Add করো", callback_data=f"upload_for_{key}"))
    bot.send_message(call.message.chat.id, "কোন প্রোডাক্টে স্টক Add করবা?", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("upload_for_"))
def upload_for(call):
    if call.from_user.id != ADMIN_ID:
        return
    key = call.data.replace("upload_for_", "")
    p = data["products"].get(key)
    if not p:
        return
    data["temp"][str(call.from_user.id)] = {"step": "prod_excel_old", "key": key}
    save()
    bot.send_message(call.message.chat.id, f"{p['name']} এর জন্য এখন Excel ফাইলটা পাঠাও।")

@bot.callback_query_handler(func=lambda c: c.data=="admin_del_list")
def del_list(call):
    if call.from_user.id != ADMIN_ID:
        return
    if not data["products"]:
        bot.send_message(call.message.chat.id, "কোনো প্রোডাক্ট নাই।")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, p in data["products"].items():
        markup.add(types.InlineKeyboardButton(f"{p['name']} Delete", callback_data=f"delprod_{key}"))
    bot.send_message(call.message.chat.id, "কোনটা Delete করবা?", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delprod_"))
def delprod_btn(call):
    if call.from_user.id != ADMIN_ID:
        return
    key = call.data.replace("delprod_", "")
    if key in data["products"]:
        del data["products"][key]
        save()
        path = f"stock_{key}.xlsx"
        if os.path.exists(path):
            os.remove(path)
        bot.send_message(call.message.chat.id, "প্রোডাক্ট Delete হইছে")

@bot.message_handler(content_types=['document'])
def handle_doc(message):
    uid = str(message.from_user.id)
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "এইখানে ফাইল পাঠানো যাবে না।")
        return
    if uid not in data["temp"]:
        return
    t = data["temp"][uid]
    if t.get("step") not in ["prod_excel", "prod_excel_old"]:
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.send_message(message.chat.id, f"ফাইল ডাউনলোড হয় নাই: {e}")
        return
    if t["step"] == "prod_excel":
        key = f"p{len(data['products'])+1}_{int(datetime.now().timestamp())}"
        path = f"stock_{key}.xlsx"
        with open(path, "wb") as f:
            f.write(downloaded)
        data["products"][key] = {"name": t["prod_name"], "price": t["prod_price"]}
        del data["temp"][uid]
        save()
        stock = count_stock(key)
        bot.send_message(message.chat.id, f"✅ প্রোডাক্ট Add হইছে!\nনাম: {t['prod_name']}\nদাম: {t['prod_price']} Tk\nস্টক: {stock} পিস")
    else:
        key = t["key"]
        path = f"stock_{key}.xlsx"
        header_old, old_rows = get_stock_rows(key) if os.path.exists(path) else (None, [])
        tmp_path = f"tmp_{uid}.xlsx"
        with open(tmp_path, "wb") as f:
            f.write(downloaded)
        try:
            wb_new = load_workbook(tmp_path)
            ws_new = wb_new.active
            new_rows_raw = list(ws_new.iter_rows(values_only=True))
        except:
            new_rows_raw = []
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        new_rows = []
        first = True
        for r in new_rows_raw:
            if not any(v is not None and str(v).strip() != "" for v in r):
                continue
            if first and is_header_row(r):
                first = False
                continue
            first = False
            new_rows.append(list(r))
        wb = Workbook()
        ws = wb.active
        if header_old:
            ws.append(header_old)
        for r in old_rows:
            ws.append(r)
        for r in new_rows:
            ws.append(r)
        wb.save(path)
        del data["temp"][uid]
        save()
        stock = count_stock(key)
        bot.send_message(message.chat.id, f"✅ স্টক Add হইছে!\nনতুন: {len(new_rows)} পিস\nমোট স্টক: {stock} পিস")

# ===== এডমিন জন্য স্ট্যাটাস - 488 লাইনে ঠিক করা হলো =====
@bot.callback_query_handler(func=lambda c: c.data=="status")
def status(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    total_users = len(data["users"])
    total_bal = 0
    for u in data["users"].values():
        total_bal += u.get("balance", 0)
    bot.send_message(call.message.chat.id, f"📊 স্ট্যাটাস\n\n👥 মোট ইউজার: {total_users}\n💰 মোট ব্যালেন্স: {total_bal} ৳")

print("Bot Starting...")
bot.infinity_polling()
