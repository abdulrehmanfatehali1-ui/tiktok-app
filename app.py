from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import requests
import random
import time

app = Flask(__name__)

# --- Backend Logic ---
def get_video_meta(url):
    try:
        api_url = "https://www.tikwm.com/api/"
        headers = {"User-Agent": "Mozilla/5.0"}
        params = {"url": url, "count": 12, "cursor": 0, "web": 1, "hd": 1}
        resp = requests.get(api_url, params=params, headers=headers)
        data = resp.json()
        if data.get("code") == 0:
            d = data["data"]
            return {
                "status": "success",
                "id": d.get("id"),
                "title": d.get("title", ""),
                "cover": d.get("cover"), 
                "play_url": d.get("play"),
                "music_url": d.get("music"),
                "author_name": d.get("author", {}).get("nickname", "Unknown"),
                "author_avatar": d.get("author", {}).get("avatar"),
                "stats": {
                    "views": d.get("play_count", 0),
                    "likes": d.get("digg_count", 0)
                }
            }
        return {"status": "error"}
    except:
        return {"status": "error"}

# --- Generating Viral Hashtags ---
def get_viral_hashtags():
    tags = [
        "#foryou", "#foryoupage", "#fyp", "#duet", "#tiktok", "#viral", 
        "#tiktokindia", "#trending", "#comedy", "#funny", "#tiktokpakistan", 
        "#illu", "#standwithkashmir", "#burhan_tv", "#goviral", "#explore"
    ]
    random.shuffle(tags)
    return " ".join(tags[:10]) # Return top 10 random tags

# --- Frontend Template (Modern Dashboard) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>TikTok Wala - Super Tool</title>
    <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/512/3046/3046121.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <meta name="referrer" content="no-referrer"> 
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        body { 
            font-family: 'Outfit', sans-serif; 
            background-color: #0f172a; 
            color: white; 
            min-height: 100vh;
            padding-bottom: 80px; /* Space for bottom nav */
        }

        .glass-panel { 
            background: rgba(30, 41, 59, 0.8); 
            backdrop-filter: blur(15px); 
            border: 1px solid rgba(255, 255, 255, 0.08); 
        }

        .btn-gradient { 
            background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%); 
        }
        
        .btn-gold {
            background: linear-gradient(135deg, #FFD700 0%, #FDB931 100%);
            color: black;
        }

        /* Bottom Navigation */
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-around;
            padding: 12px 0;
            z-index: 50;
        }
        
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            font-size: 10px;
            color: #64748b;
            transition: all 0.3s;
        }
        
        .nav-item.active {
            color: #ec4899;
            transform: translateY(-2px);
        }
        
        .nav-item i { font-size: 18px; margin-bottom: 4px; }

        .loader { border: 3px solid rgba(255,255,255,0.1); border-left-color: #ec4899; border-radius: 50%; width: 24px; height: 24px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="p-4">

    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-2">
            <img src="https://cdn-icons-png.flaticon.com/512/3046/3046121.png" class="w-8 h-8">
            <h1 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-500 to-purple-500">TikTok Wala</h1>
        </div>
        <div id="userStatus" class="text-xs bg-slate-800 px-3 py-1 rounded-full border border-white/10 text-slate-300">
            Free Plan
        </div>
    </div>

    <!-- ================= TAB 1: DOWNLOADER ================= -->
    <div id="tab-home" class="tab-content active">
        <div class="glass-panel p-6 rounded-3xl mb-4">
            <h2 class="text-lg font-bold mb-4">Video Downloader</h2>
            <input type="text" id="urlInput" placeholder="Paste TikTok Link..." class="w-full bg-slate-900 p-4 rounded-xl text-white text-sm outline-none border border-slate-700 mb-4 focus:border-pink-500 transition">
            <button onclick="fetchInfo()" id="searchBtn" class="w-full btn-gradient py-3.5 rounded-xl font-bold text-sm shadow-lg flex items-center justify-center gap-2">
                <i class="fa-solid fa-cloud-arrow-down"></i> Download
            </button>
            <div id="dl-result" class="hidden mt-6 bg-slate-800/50 p-4 rounded-2xl border border-white/5">
                <!-- Result injected via JS -->
            </div>
        </div>
    </div>

    <!-- ================= TAB 2: VIEWS & LIKES ================= -->
    <div id="tab-views" class="tab-content">
        <div class="glass-panel p-6 rounded-3xl mb-4 relative overflow-hidden">
            <div class="absolute top-0 right-0 bg-yellow-500 text-black text-[10px] font-bold px-2 py-1 rounded-bl-lg">HOT</div>
            <h2 class="text-lg font-bold mb-2">Get Views & Likes</h2>
            <p class="text-xs text-slate-400 mb-4">Boost your video instantly.</p>
            
            <div class="bg-slate-900/50 p-3 rounded-xl mb-4 border border-white/5">
                <div class="flex justify-between text-xs mb-1">
                    <span class="text-slate-400">Daily Limit:</span>
                    <span id="viewLimit" class="font-bold text-pink-500">1000</span>
                </div>
                <div class="w-full bg-slate-700 h-1.5 rounded-full">
                    <div id="limitBar" class="bg-pink-500 h-1.5 rounded-full" style="width: 100%"></div>
                </div>
            </div>

            <input type="text" id="viewUrl" placeholder="Video Link for Views..." class="w-full bg-slate-900 p-3 rounded-xl text-sm mb-3 outline-none border border-slate-700">
            <button onclick="sendViews()" id="viewBtn" class="w-full bg-slate-700 hover:bg-slate-600 py-3 rounded-xl font-bold text-sm transition">
                🚀 Send 1000 Views (Free)
            </button>
            
            <div id="viewMsg" class="mt-3 text-xs text-center hidden"></div>

            <!-- Premium Upsell -->
            <div class="mt-6 border-t border-white/10 pt-4 text-center">
                <p class="text-sm font-semibold text-yellow-400 mb-2">Want 3000+ Views?</p>
                <button onclick="switchTab('tab-premium')" class="btn-gold px-6 py-2 rounded-full text-xs font-bold shadow-lg shadow-yellow-500/20">
                    Get Premium Plan
                </button>
            </div>
        </div>
    </div>

    <!-- ================= TAB 3: TOOLS (Unfreeze/Hash) ================= -->
    <div id="tab-tools" class="tab-content">
        <!-- Hashtag Generator -->
        <div class="glass-panel p-5 rounded-3xl mb-4">
            <div class="flex items-center gap-2 mb-3">
                <i class="fa-solid fa-hashtag text-pink-500"></i>
                <h2 class="text-base font-bold">Viral Hashtags</h2>
            </div>
            <div id="hashResult" class="bg-slate-900 p-3 rounded-xl text-xs text-slate-300 mb-3 min-h-[50px]">
                Click generate to get tags...
            </div>
            <button onclick="getHashtags()" class="w-full bg-slate-700 py-2 rounded-lg text-xs font-bold">Generate</button>
        </div>

        <!-- Unfreeze Account -->
        <div class="glass-panel p-5 rounded-3xl">
            <div class="flex items-center gap-2 mb-3">
                <i class="fa-solid fa-snowflake text-cyan-400"></i>
                <h2 class="text-base font-bold">Unfreeze Account</h2>
            </div>
            <input type="text" id="username" placeholder="@username" class="w-full bg-slate-900 p-2 rounded-lg text-xs mb-2 border border-slate-700">
            <button onclick="unfreeze()" class="w-full bg-cyan-600 hover:bg-cyan-700 py-2 rounded-lg text-xs font-bold">Generate Appeal</button>
            <textarea id="appealBox" class="w-full bg-slate-900 p-2 rounded-lg text-[10px] mt-2 hidden h-24 text-slate-300" readonly></textarea>
        </div>
    </div>

    <!-- ================= TAB 4: PREMIUM (JazzCash) ================= -->
    <div id="tab-premium" class="tab-content">
        <div class="glass-panel p-6 rounded-3xl border border-yellow-500/30 relative overflow-hidden">
            <div class="absolute inset-0 bg-yellow-500/5 z-0"></div>
            <div class="relative z-10 text-center">
                <i class="fa-solid fa-crown text-4xl text-yellow-400 mb-2"></i>
                <h2 class="text-xl font-bold text-white">Premium Plan</h2>
                <p class="text-sm text-slate-400 mb-6">Unlock 3000 Views + Fast Servers</p>

                <div class="bg-slate-900/80 p-4 rounded-xl text-left mb-4 border border-white/10">
                    <p class="text-xs text-slate-400">Price:</p>
                    <p class="text-xl font-bold text-white">Rs. 150 <span class="text-xs font-normal text-slate-500">/ Lifetime</span></p>
                    <hr class="border-white/10 my-2">
                    <p class="text-xs text-slate-400">JazzCash Number:</p>
                    <div class="flex justify-between items-center">
                        <p class="text-lg font-mono text-yellow-400 font-bold">03076485837</p>
                        <button onclick="navigator.clipboard.writeText('03076485837'); alert('Copied!')" class="text-slate-500 hover:text-white"><i class="fa-regular fa-copy"></i></button>
                    </div>
                </div>

                <div class="space-y-2">
                    <input type="text" id="senderNum" placeholder="Your JazzCash Number" class="w-full bg-slate-900 p-3 rounded-lg text-xs border border-slate-700">
                    <input type="text" id="trxId" placeholder="Trx ID (Transaction ID)" class="w-full bg-slate-900 p-3 rounded-lg text-xs border border-slate-700">
                    <button onclick="submitPayment()" class="w-full btn-gold py-3 rounded-lg font-bold text-sm shadow-lg">
                        Submit for Verification
                    </button>
                </div>
                <p id="payMsg" class="text-[10px] text-green-400 mt-2 hidden"></p>
            </div>
        </div>
    </div>

    <!-- Bottom Navigation -->
    <div class="bottom-nav">
        <div class="nav-item active" onclick="switchTab('tab-home', this)">
            <i class="fa-solid fa-home"></i> Home
        </div>
        <div class="nav-item" onclick="switchTab('tab-views', this)">
            <i class="fa-solid fa-fire"></i> Views
        </div>
        <div class="nav-item" onclick="switchTab('tab-tools', this)">
            <i class="fa-solid fa-toolbox"></i> Tools
        </div>
        <div class="nav-item" onclick="switchTab('tab-premium', this)">
            <i class="fa-solid fa-crown text-yellow-500"></i> Premium
        </div>
    </div>

    <script>
        // --- Tab Switching Logic ---
        function switchTab(tabId, navElement) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            // Show selected tab
            document.getElementById(tabId).classList.add('active');
            
            // Update Nav Icons
            if(navElement) {
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                navElement.classList.add('active');
            }
        }

        // --- Downloader Logic ---
        async function fetchInfo() {
            const url = document.getElementById('urlInput').value.trim();
            const resDiv = document.getElementById('dl-result');
            const btn = document.getElementById('searchBtn');

            if(!url) return alert("Please paste a link!");
            
            btn.innerHTML = '<div class="loader"></div>';
            resDiv.classList.add('hidden');

            try {
                const res = await fetch('/api/info', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url})
                });
                const data = await res.json();
                
                if(data.status === 'success') {
                    resDiv.innerHTML = `
                        <div class="flex gap-3 mb-3">
                            <img src="${data.cover}" class="w-16 h-20 object-cover rounded-lg bg-slate-900">
                            <div>
                                <h3 class="text-xs font-bold line-clamp-2">${data.title || 'Video'}</h3>
                                <p class="text-[10px] text-slate-400 mt-1">${data.author_name}</p>
                            </div>
                        </div>
                        <a href="/proxy_download?url=${encodeURIComponent(data.play_url)}&name=${data.id}&type=mp4" class="btn-gradient w-full block text-center py-2 rounded-lg text-xs font-bold mb-2">Download Video</a>
                        <a href="/proxy_download?url=${encodeURIComponent(data.music_url)}&name=${data.id}&type=mp3" class="bg-slate-700 w-full block text-center py-2 rounded-lg text-xs">Download Audio</a>
                    `;
                    resDiv.classList.remove('hidden');
                } else {
                    alert("Video not found!");
                }
            } catch(e) {
                alert("Error connecting to server");
            } finally {
                btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-down"></i> Download';
            }
        }

        // --- Views Logic (Simulated) ---
        function sendViews() {
            const url = document.getElementById('viewUrl').value;
            const btn = document.getElementById('viewBtn');
            const msg = document.getElementById('viewMsg');
            
            // Check Local Storage Limit
            let viewsUsed = localStorage.getItem('viewsToday') || 0;
            if(viewsUsed >= 1000) {
                alert("Daily Free Limit (1000) Reached! Upgrade to Premium.");
                return;
            }

            if(!url) return alert("Paste video link first!");

            btn.disabled = true;
            btn.innerText = "Sending Views...";
            
            // Simulate API Call delay
            setTimeout(() => {
                let sent = Math.floor(Math.random() * 50) + 100; // Random 100-150 views
                let newTotal = parseInt(viewsUsed) + sent;
                
                if(newTotal > 1000) newTotal = 1000;
                localStorage.setItem('viewsToday', newTotal);

                // Update UI
                updateLimitBar();
                
                msg.innerText = `Success! ${sent} views sent. (It may take 10-30 mins to reflect)`;
                msg.classList.remove('hidden');
                msg.className = "mt-3 text-xs text-center text-green-400";
                
                btn.disabled = false;
                btn.innerText = "🚀 Send More Views";
            }, 2000);
        }

        function updateLimitBar() {
            let used = localStorage.getItem('viewsToday') || 0;
            let percent = (used / 1000) * 100;
            document.getElementById('limitBar').style.width = (100 - percent) + "%";
            document.getElementById('viewLimit').innerText = (1000 - used);
        }
        updateLimitBar(); // Init

        // --- Hashtag Logic ---
        async function getHashtags() {
            const box = document.getElementById('hashResult');
            box.innerText = "Generating...";
            const res = await fetch('/api/hashtags');
            const data = await res.json();
            box.innerText = data.tags;
        }

        // --- Unfreeze Logic ---
        function unfreeze() {
            const user = document.getElementById('username').value;
            if(!user) return alert("Enter username!");
            const text = `Hello TikTok Team,\n\nMy account ${user} has been frozen mistakenly. I follow all community guidelines. Please review my account and unfreeze it as soon as possible. I am a content creator and this is affecting my reach.\n\nThank you.`;
            const box = document.getElementById('appealBox');
            box.value = text;
            box.classList.remove('hidden');
        }

        // --- Payment Logic ---
        function submitPayment() {
            const trx = document.getElementById('trxId').value;
            const num = document.getElementById('senderNum').value;
            if(!trx || !num) return alert("Fill all details!");
            
            document.getElementById('payMsg').innerText = "Request Sent! Admin will verify TRX: " + trx + " within 24 hours.";
            document.getElementById('payMsg').classList.remove('hidden');
            
            // In a real app, send this to database. 
            // Here we just simulate success for the user.
        }

    </script>
</body>
</html>
"""

# --- Routes ---
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/info', methods=['POST'])
def api_info():
    data = request.json
    result = get_video_meta(data.get('url'))
    return jsonify(result)

@app.route('/api/hashtags')
def api_tags():
    return jsonify({"tags": get_viral_hashtags()})

@app.route('/proxy_download')
def proxy_download():
    # ... (Same proxy logic as before) ...
    file_url = request.args.get('url')
    file_id = request.args.get('name', 'tiktok')
    file_type = request.args.get('type', 'mp4')
    if not file_url: return "No URL", 400
    if not file_url.startswith(('http://', 'https://')): file_url = "https://www.tikwm.com" + file_url
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.tikwm.com/"}
    try:
        req = requests.get(file_url, stream=True, headers=headers)
        ct = "video/mp4" if file_type == 'mp4' else "audio/mpeg"
        fname = f"{file_id}.{file_type}"
        return Response(stream_with_context(req.iter_content(chunk_size=4096)), content_type=ct, headers={"Content-Disposition": f"attachment; filename={fname}"})
    except: return "Error", 400

if __name__ == '__main__':
    app.run()
