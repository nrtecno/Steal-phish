cd ~/Steal-phish

# Remove .env if exists
rm -f phishing-server/.env phishing-server/.env.example

# Add all files
git add .
git commit -m "Final: Secure Share without .env files"
git push origin main
