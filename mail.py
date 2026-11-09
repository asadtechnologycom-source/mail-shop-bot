import telebot
from telebot import types
import json, os
from openpyxl import Workbook, load_workbook
from datetime import datetime
from flask import Flask
from threading import Thread

# ---------- RENDER LIVE থাকার জন্য - এটা মুছবা না ----------
app = Flask(__name__)
@app.route('/')
def home():
    return "MAIL SHOP BD Bot is Live!"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
Thread(target=run_web, daemon=True).start()
# -------------------------------------------------------

BOT_TOKEN = "8984459858:AAGp4YVV91muymq0ErICTulevJ-ZSsT31ds"
ADMIN_ID = 7952385899
ADMIN_USERNAME = "@DULU_VAI"
bot = telebot.TeleBot(BOT_TOKEN)

# ---------- DATA ----------
DEFAULT_DASH = """╔═══════════════════════╗
║ 💎 MAIL SHOP BD 💎 ║
║ ✨ VERIFIED BOT ✨ ║
╚═══════════════════════╝
🌟 ━━━ WELCOME ━━━ 🌟
┏━ 👤 USER INFORMATION ━┓
┃ 👑 Name: {name}
┃ 💌 Username: {username}
┃ 🆔 ID: {uid}
┃ 💰 Balance: {bal:.2f} Tk
┗━━━━━━━━━━━━━━━━━━━━━┛

🛒 নিচ থেকে প্রোডাক্ট সিলেক্ট করে কিনো।
💳 আগে ডিপোজিট করো, তারপর কিনতে পারবা।"""

def save():
    json.dump(data, open("data.json","w"))

if not os.path.exists("data.json"):
    data = {"products": {}, "users": {}, "payments": {}, "channels": [], "temp": {}, "orders": {}, "settings": {"dashboard": DEFAULT_DASH, "banner": None}}
    json.dump(data, open("data.json","w"))
else:
    data = json.load(open("data.json"))

# পুরানো data.json এ settings না থাকলে যোগ হবে
if "settings" not in data:
    data["settings"] = {"dashboard": DEFAULT_DASH, "banner": None}
if "temp" not in data:
    data["temp"] = {}
if "orders" not in data:
    data["orders"] = {}
save()

def get_user(uid, msg=None):
    uid = str(uid)
    if uid not in data["users"]:
        name = msg.from_user.first_name if msg else ""
        username = msg.from_user.username or "" if msg else ""
        data["users"][uid] = {"balance": 0, "name": name, "username": username, "bought": [], "bought_count": 0}
        save()
    return data["users"][uid]

def count_stock(key):
    path = f"stock_{key}.xlsx"
    if not os.path.exists(path): return 0
    try:
        wb = load_workbook(path); ws = wb.active; c = 0
        for row in ws.iter_rows(values_only=True):
            if any(v is not None and str(v).strip() != "" for v in row): c += 1
        return c
    except: return 0

def check_join(uid):
    for ch in data["channels"]:
        try:
            m = bot.get_chat_member(ch, int(uid))
            if m.status in ["left", "kicked"]: return False
        except: return False
    return True

def join_markup():
    markup = types.InlineKeyboardMarkup()
    for ch in data["channels"]:
        markup.add(types.InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch.replace('@','')}"))
    markup.add(types.InlineKeyboardButton("Join করছি, Check করো", callback_data="check_join"))
    return markup

# ---------- START / MENU ----------
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    get_user(uid, message)
    if data["channels"] and not check_join(uid):
        bot.send_message(message.chat.id, "আগে চ্যানেলে জয়েন করো!", reply_markup=join_markup())
        return
    show_menu(message.chat.id, uid, message)

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
        except: pass
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data=="check_join")
def check_join_btn(call):
    uid = str(call.from_user.id)
    if check_join(uid):
        bot.send_message(call.message.chat.id, "জয়েন হইছে!")
        show_menu(call.message.chat.id, uid, call)
    else:
        bot.answer_callback_query(call.id, "এখনো জয়েন করো নাই!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data=="mybal")
def mybal(call):
    u = get_user(call.from_user.id)
    bot.answer_callback_query(call.id, f"তোমার ব্যালেন্স: {u['balance']} Tk", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data=="back_menu")
def back_menu(call):
    show_menu(call.message.chat.id, str(call.from_user.id), call)

# ---------- ADMIN PANEL ----------
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("✏️ ড্যাশবোর্ড মেসেজ চেঞ্জ", callback_data="admin_change_dash"))
    markup.add(types.InlineKeyboardButton("🖼️ ব্যানার চেঞ্জ", callback_data="admin_change_banner"))
    markup.add(types.InlineKeyboardButton("➕ প্রোডাক্ট Add", callback_data="admin_add_product"))
    markup.add(types.InlineKeyboardButton("🗑️ প্রোডাক্ট Delete", callback_data="admin_del_list"))
    markup.add(types.InlineKeyboardButton("📤 Excel Upload / স্টক Add", callback_data="admin_upload_list"))
    markup.add(types.InlineKeyboardButton("📢 সবাইকে মেসেজ (Broadcast)", callback_data="broadcast_start"))
    markup.add(types.InlineKeyboardButton("📊 Status", callback_data="status"))
    markup.add(types.InlineKeyboardButton("📥 Receive - Excel (সব মেম্বার)", callback_data="receive_excel"))
    bot.send_message(message.chat.id, f"👑 এডমিন প্যানেল - {ADMIN_USERNAME}\n\nপেমেন্ট: /addpayment bkash 016XXX | /delpayment bkash\nচ্যানেল: /addchannel @mychannel | /delchannel @mychannel", reply_markup=markup)

# --- DASHBOARD CHANGE ---
@bot.callback_query_handler(func=lambda c: c.data=="admin_change_dash")
def change_dash_start(call):
    if call.from_user.id != ADMIN_ID: return
    data["temp"][str(call.from_user.id)] = {"step": "change_dash"}; save()
    bot.send_message(call.message.chat.id, "✏️ ড্যাশবোর্ড মেসেজ চেঞ্জ করো\n\nএখন নতুন মেসেজটা লিখে পাঠাও।\n\nতুমি এই ৪টা ব্যবহার করতে পারবা:\n{name} = নাম\n{username} = ইউজারনেম\n{uid} = আইডি\n{bal} = ব্যালেন্স")

@bot.message_handler(func=lambda m: str(m.from_user.id) in data["temp"] and data["temp"][str(m.from_user.id)].get("step")=="change_dash")
def change_dash_save(message):
    if message.from_user.id != ADMIN_ID: return
    data["settings"]["dashboard"] = message.text
    del data["temp"][str(message.from_user.id)]; save()
    bot.send_message(message.chat.id, "✅ ড্যাশবোর্ড মেসেজ চেঞ্জ হইছে! এখন /start দিয়ে দেখো।")

# --- BANNER CHANGE ---
@bot.callback_query_handler(func=lambda c: c.data=="admin_change_banner")
def change_banner_start(call):
    if call.from_user.id != ADMIN_ID: return
    data["temp"][str(call.from_user.id)] = {"step": "change_banner"}; save()
    bot.send_message(call.message.chat.id, "🖼️ ব্যানার চেঞ্জ করো\n\nএখন নতুন ব্যানার ছবিটা পাঠাও।")

@bot.message_handler(commands=['addchannel'])
def addch(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, ch = message.text.split()
        if ch not in data["channels"]: data["channels"].append(ch); save()
        bot.send_message(message.chat.id, f"চ্যানেল Add: {ch}")
    except: bot.send_message(message.chat.id, "ভুল! /addchannel @mychannel")

@bot.message_handler(commands=['delchannel'])
def delch(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, ch = message.text.split()
        data["channels"].remove(ch); save()
        bot.send_message(message.chat.id, "চ্যানেল Delete হইছে")
    except: bot.send_message(message.chat.id, "ভুল! /delchannel @mychannel")

@bot.message_handler(commands=['addpayment'])
def addpay(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, key, num = message.text.split()
        data["payments"][key.lower()] = num; save()
        bot.send_message(message.chat.id, f"পেমেন্ট Add: {key} - {num}")
    except: bot.send_message(message.chat.id, "ভুল! /addpayment bkash 016XXX")

@bot.message_handler(commands=['delpayment'])
def delpay(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, key = message.text.split(); del data["payments"][key.lower()]; save()
        bot.send_message(message.chat.id, "ডিলিট হইছে")
    except: bot.send_message(message.chat.id, "ভুল! /delpayment bkash")

# ---------- ADMIN: ADD PRODUCT ----------
@bot.callback_query_handler(func=lambda c: c.data=="admin_add_product")
def admin_add_start(call):
    if call.from_user.id != ADMIN_ID: return
    data["temp"][str(call.from_user.id)] = {"step": "prod_name"}; save()
    bot.send_message(call.message.chat.id, "➕ নতুন প্রোডাক্ট Add\n\nপ্রোডাক্টের নাম কি? যেমন: Fresh Gmail 2024")

@bot.message_handler(func=lambda m: str(m.from_user.id) in data["temp"] and data["temp"][str(m.from_user.id)].get("step")=="prod_name")
def prod_name_step(message):
    if message.from_user.id != ADMIN_ID: return
    uid = str(message.from_user.id)
    data["temp"][uid]["prod_name"] = message.text.strip(); data["temp"][uid]["step"] = "prod_price"; save()
    bot.send_message(message.chat.id, f"নাম: {message.text}\n\nএখন দাম কত? পার পিস দাম লিখো। যেমন: 50")

@bot.message_handler(func=lambda m: str(m.from_user.id) in data["temp"] and data["temp"][str(m.from_user.id)].get("step")=="prod_price")
def prod_price_step(message):
    if message.from_user.id != ADMIN_ID: return
    uid = str(message.from_user.id)
    try: price = int(message.text.strip())
    except: bot.send_message(message.chat.id, "শুধু সংখ্যা লিখো। যেমন: 50"); return
    data["temp"][uid]["prod_price"] = price; data["temp"][uid]["step"] = "prod_excel"; save()
    bot.send_message(message.chat.id, f"দাম: {price} Tk / পিস\n\nএখন Excel ফাইলটা পাঠাও।\n\n১ লাইন = ১ পিস।")

@bot.callback_query_handler(func=lambda c: c.data=="admin_upload_list")
def upload_list(call):
    if call.from_user.id != ADMIN_ID: return
    if not data["products"]:
        bot.send_message(call.message.chat.id, "কোনো প্রোডাক্ট নাই।"); return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, p in data["products"].items():
        markup.add(types.InlineKeyboardButton(f"{p['name']} - স্টক Add করো", callback_data=f"upload_for_{key}"))
    bot.send_message(call.message.chat.id, "কোন প্রোডাক্টে Excel / স্টক Add করবা?", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("upload_for_"))
def upload_for(call):
    if call.from_user.id != ADMIN_ID: return
    key = call.data.replace("upload_for_", ""); p = data["products"].get(key)
    if not p: return
    data["temp"][str(call.from_user.id)] = {"step": "prod_excel_old", "key": key}; save()
    bot.send_message(call.message.chat.id, f"{p['name']} এর জন্য এখন Excel ফাইলটা পাঠাও।")

@bot.callback_query_handler(func=lambda c: c.data=="admin_del_list")
def del_list(call):
    if call.from_user.id != ADMIN_ID: return
    if not data["products"]:
        bot.send_message(call.message.chat.id, "কোনো প্রোডাক্ট নাই।"); return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, p in data["products"].items():
        markup.add(types.InlineKeyboardButton(f"{p['name']} Delete", callback_data=f"delprod_{key}"))
    bot.send_message(call.message.chat.id, "কোনটা Delete করবা?", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delprod_"))
def delprod_btn(call):
    if call.from_user.id != ADMIN_ID: return
    key = call.data.replace("delprod_", "")
    if key in data["products"]:
        del data["products"][key]; save()
        path = f"stock_{key}.xlsx"
        if os.path.exists(path): os.remove(path)
        bot.send_message(call.message.chat.id, "প্রোডাক্ট Delete হইছে")

# ---------- HANDLE EXCEL DOCUMENT ----------
@bot.message_handler(content_types=['document'])
def handle_doc(message):
    uid = str(message.from_user.id)
    if message.from_user.id != ADMIN_ID: return
    if uid not in data["temp"]: return
    t = data["temp"][uid]
    if t.get("step") not in ["prod_excel", "prod_excel_old"]: return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.send_message(message.chat.id, f"ফাইল ডাউনলোড হয় নাই: {e}"); return
    if t["step"] == "prod_excel":
        key = f"p{len(data['products'])+1}_{int(datetime.now().timestamp())}"
        path = f"stock_{key}.xlsx"
        with open(path, "wb") as f: f.write(downloaded)
        data["products"][key] = {"name": t["prod_name"], "price": t["prod_price"]}
        del data["temp"][uid]; save()
        stock = count_stock(key)
        bot.send_message(message.chat.id, f"✅ প্রোডাক্ট Add হইছে!\n\nনাম: {t['prod_name']}\nদাম: {t['prod_price']} Tk / পিস\nস্টক: {stock} পিস")
    else:
        key = t["key"]; path = f"stock_{key}.xlsx"
        if os.path.exists(path):
            try:
                wb_old = load_workbook(path); ws_old = wb_old.active
                old_rows = list(ws_old.iter_rows(values_only=True))
            except: old_rows = []
        else: old_rows = []
        tmp_path = f"tmp_{uid}.xlsx"
        with open(tmp_path, "wb") as f: f.write(downloaded)
        try:
            wb_new = load_workbook(tmp_path); ws_new = wb_new.active
            new_rows = list(ws_new.iter_rows(values_only=True))
        except: new_rows = []
        if os.path.exists(tmp_path): os.remove(tmp_path)
        wb = Workbook(); ws = wb.active
        for r in old_rows:
            if any(v is not None and str(v).strip() != "" for v in r): ws.append(list(r))
        added = 0
        for r in new_rows:
            if any(v is not None and str(v).strip() != "" for v in r): ws.append(list(r)); added += 1
        wb.save(path); del data["temp"][uid]; save()
        stock = count_stock(key)
        bot.send_message(message.chat.id, f"✅ স্টক Add হইছে!\n\nনতুন যোগ হইছে: {added} পিস\nএখন মোট স্টক: {stock} পিস")

# ---------- STATUS / RECEIVE / BROADCAST ----------
@bot.callback_query_handler(func=lambda c: c.data=="status")
def status(call):
    if call.from_user.id != ADMIN_ID: return
    total_users = len(data["users"])
    total_bal = sum(u["balance"] for u in data["users"].values())
    total_sold = sum(u["bought_count"] for u in data["users"].values())
    total_stock = sum(count_stock(k) for k in data["products"].keys())
    bot.send_message(call.message.chat.id, f"📊 STATUS\n\nমোট মেম্বার: {total_users}\nমোট ব্যালেন্স: {total_bal} Tk\nমোট বিক্রি: {total_sold} টি\nমোট প্রোডাক্ট: {len(data['products'])} টি\nমোট স্টক: {total_stock} পিস")

@bot.callback_query_handler(func=lambda c: c.data=="receive_excel")
def receive_excel(call):
    if call.from_user.id != ADMIN_ID: return
    wb = Workbook(); ws = wb.active; ws.title = "Members"
    ws.append(["Telegram ID", "নাম", "ইউজারনেম", "ব্যালেন্স (Tk)", "কয়টা কিনছে", "কি কি প্রোডাক্ট কিনছে"])
    for uid, u in data["users"].items():
        bought_str = ", ".join(u.get("bought", [])) if u.get("bought") else "কিছু কিনে নাই"
        ws.append([uid, u.get("name",""), "@"+u.get("username","") if u.get("username") else "", u.get("balance",0), u.get("bought_count",0), bought_str])
    wb.save("all_members.xlsx")
    with open("all_members.xlsx","rb") as f:
        bot.send_document(call.message.chat.id, f, caption="সব মেম্বারের ডিটেইলস")

@bot.callback_query_handler(func=lambda c: c.data=="broadcast_start")
def bc_start(call):
    if call.from_user.id != ADMIN_ID: return
    data["temp"][str(call.from_user.id)] = {"step": "broadcast"}; save()
    bot.send_message(call.message.chat.id, "সবাইকে কি মেসেজ পাঠাবা?\nএখন মেসেজটা লিখে পাঠাও।")

@bot.message_handler(func=lambda m: str(m.from_user.id) in data["temp"] and data["temp"][str(m.from_user.id)].get("step")=="broadcast")
def bc_send(message):
    if message.from_user.id != ADMIN_ID: return
    del data["temp"][str(message.from_user.id)]; save()
    count = 0
    for uid in list(data["users"].keys()):
        try:
            bot.send_message(int(uid), f"MAIL SHOP BD থেকে মেসেজ:\n\n{message.text}"); count += 1
        except: pass
    bot.send_message(message.chat.id, f"Broadcast শেষ! {count} জনকে পাঠানো হইছে।")

# ---------- DEPOSIT ----------
@bot.callback_query_handler(func=lambda c: c.data=="deposit")
def deposit_start(call):
    if not data["payments"]:
        bot.send_message(call.message.chat.id, "পেমেন্ট মেথড নাই।"); return
    markup = types.InlineKeyboardMarkup(row_width=2)
    for key in data["payments"]:
        markup.add(types.InlineKeyboardButton(f"{key.upper()}", callback_data=f"pay_{key}"))
    bot.send_message(call.message.chat.id, "পেমেন্ট মেথড সিলেক্ট করো:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_"))
def pay_select(call):
    method = call.data.replace("pay_", ""); uid = str(call.from_user.id)
    data["temp"][uid] = {"method": method, "step": "amount"}; save()
    bot.send_message(call.message.chat.id, f"{method.upper()} সিলেক্ট করছো।\nএখন কত টাকা ডিপোজিট করবা লিখো। যেমন: 100")

@bot.message_handler(func=lambda m: str(m.from_user.id) in data["temp"] and data["temp"][str(m.from_user.id)].get("step")=="amount")
def get_amount(message):
    uid = str(message.from_user.id)
    try: amount = int(message.text)
    except: bot.send_message(message.chat.id, "শুধু সংখ্যা লিখো"); return
    method = data["temp"][uid]["method"]; number = data["payments"].get(method, "")
    data["temp"][uid]["amount"] = amount; data["temp"][uid]["step"] = "trxid"; save()
    bot.send_message(message.chat.id, f"পেমেন্ট করো:\n\nমেথড: {method.upper()}\nনাম্বার: {number}\nএমাউন্ট: {amount} Tk\n\nটাকা পাঠিয়ে তোমার Transaction ID লিখে পাঠাও।")

@bot.message_handler(func=lambda m: str(m.from_user.id) in data["temp"] and data["temp"][str(m.from_user.id)].get("step")=="trxid")
def get_trx(message):
    uid = str(message.from_user.id)
    data["temp"][uid]["trxid"] = message.text; data["temp"][uid]["step"] = "screenshot"; save()
    bot.send_message(message.chat.id, "TrxID পেয়েছি। এখন স্ক্রিনশট পাঠাও।")

@bot.message_handler(content_types=['photo'])
def get_photo(message):
    uid = str(message.from_user.id)
    if uid not in data["temp"]: return
    step = data["temp"][uid].get("step")
    if message.from_user.id == ADMIN_ID and step == "change_banner":
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded = bot.download_file(file_info.file_path)
            with open("banner.jpg","wb") as f: f.write(downloaded)
            data["settings"]["banner"] = "banner.jpg"
            del data["temp"][uid]; save()
            bot.send_message(message.chat.id, "✅ ব্যানার চেঞ্জ হইছে! এখন /start দিয়ে দেখো।")
        except Exception as e:
            bot.send_message(message.chat.id, f"ব্যানার সেভ হয় নাই: {e}")
        return
    if step != "screenshot": return
    t = data["temp"][uid]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Approve", callback_data=f"approve_{uid}_{t['amount']}"),
            
