cd ~/Steal-phish

# Remove shared directory
rm -rf shared

# Add updated files
git add bot/bot.py phishing-server/server.js
git commit -m "Fix: Database path to bot directory"
git push origin main
