cd ~/Steal-phish

# Add new files and update
git add runtime.txt bot/bot.py bot/requirements.txt
git commit -m "Fix: Pin Python 3.11, use pyTelegramBotAPI instead of aiogram"
git push origin main
