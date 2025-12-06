from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import requests
import random
import time
import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key_tiktok_pro"

# --- Backend Logic (Downloader) ---
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
                "stats": {
                    "views": d.get("play_count", 0),
                    "likes": d.get("digg_count", 0)
                }
            }
        return {"status": "error"}
    except:
        return {"status": "error"}

# --- UI Template (Cyberpunk Dashboard) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>TikTok GOD MODE</title>
    <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/512/3046/3046121.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&display=swap');
        
        body { 
            font-family: 'Rajdhani', sans-serif; 
            background-color: #050505; 
            color: #00ff9d; 
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Cyberpunk Grid Background */
        .cyber-bg {
            background-image: linear-gradient(rgba(0, 255, 157, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 157, 0.05) 1px, transparent 1px);
            background-size: 30px 30px;
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
        }

        .glass-box {
            background: rgba(10, 20, 15, 0.8);
            border: 1px solid #00ff9d;
            box-shadow: 0 0 15px rgba(0, 255, 157, 0.2);
            backdrop-filter: blur(10px);
        }

        .neon-text { text-shadow: 0 0 10px rgba(0, 255, 157, 0.7); }
        .neon-btn {
            background: #00ff9d; color: black; font-weight: bold; text-transform: uppercase;
            box-shadow: 0 0 20px rgba(0, 255, 157, 0.4); transition: 0.3s;
        }
        .neon-btn:hover { box-shadow: 0 0 40px rgba(0, 255, 157, 0.8); transform: scale(1.02); }

        .input-cyber {
            background: black; border: 1px solid #333; color: white;
            font-family: 'Courier New', monospace;
        }
        .input-cyber:focus { border-color: #00ff9d; outline: none; }

        /* Console Animation */
        .console-log {
            font-family: 'Courier New', monospace; font-size: 10px; color: #00ff9d;
            height: 150px; overflow-y: auto; background: black; border: 1px solid #333;
            padding: 10px; opacity: 0.8;
        }
        
        .hidden { display: none; }
        .fade-in { animation: fadeIn 0.5s ease-in-out; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

        /* Progress Bar */
        .progress-container { width: 100%; background: #222; height: 10px; border-radius: 5px; margin-top: 10px; overflow: hidden; }
        .progress-bar { height: 100%; background: #00ff9d; width: 0%; transition: width 0.2s; box-shadow: 0 0 10px #00ff9d; }
    </style>
</head>
<body class="flex items-center justify-center p-4">

    <div class="cyber-bg"></div>

    <!-- ================= AUTH SCREEN (Login/Signup) ================= -->
    <div id="authScreen" class="w-full max-w-sm glass-box p-8 rounded-none relative fade-in">
        <div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-black px-4 text-[#00ff9d] border border-[#00ff9d] text-xs font-bold tracking-widest">
            SECURE ACCESS
        </div>
        
        <div class="text-center mb-8">
            <i class="fa-solid fa-user-secret text-5xl mb-2 neon-text"></i>
            <h1 class="text-3xl font-bold tracking-wider">TIKTOK GOD</h1>
            <p class="text-xs text-gray-500">SYSTEM V.9.0 // READY</p>
        </div>

        <div id="loginForm">
            <input type="text" id="l_user" placeholder="USERNAME" class="w-full input-cyber p-3 mb-4 text-sm">
            <input type="password" id="l_pass" placeholder="PASSWORD" class="w-full input-cyber p-3 mb-6 text-sm">
            <button onclick="handleLogin()" class="w-full neon-btn p-3 tracking-widest mb-4">LOGIN SYSTEM</button>
            <p class="text-center text-xs cursor-pointer hover:text-white" onclick="toggleAuth()">Create New Account</p>
        </div>

        <div id="signupForm" class="hidden">
            <input type="text" id="s_user" placeholder="SET USERNAME" class="w-full input-cyber p-3 mb-4 text-sm">
            <input type="password" id="s_pass" placeholder="SET PASSWORD" class="w-full input-cyber p-3 mb-6 text-sm">
            <button onclick="handleSignup()" class="w-full neon-btn p-3 tracking-widest mb-4">REGISTER ID</button>
            <p class="text-center text-xs cursor-pointer hover:text-white" onclick="toggleAuth()">Back to Login</p>
        </div>
    </div>

    <!-- ================= DASHBOARD SCREEN ================= -->
    <div id="dashboard" class="w-full max-w-md hidden fade-in">
        
        <!-- Top Bar -->
        <div class="glass-box p-3 mb-4 flex justify-between items-center">
            <div class="flex items-center gap-2">
                <div class="w-2 h-2 bg-[#00ff9d] rounded-full animate-pulse"></div>
                <span class="text-xs font-bold" id="displayUser">USER</span>
            </div>
            <button onclick="logout()" class="text-xs bg-red-900/50 text-red-400 px-2 py-1 border border-red-500 hover:bg-red-500 hover:text-black transition">LOGOUT</button>
        </div>

        <!-- MAIN TOOLS -->
        <div class="glass-box p-6 relative mb-4">
            <h2 class="text-xl font-bold mb-4 border-b border-[#00ff9d]/30 pb-2">TOOLKIT MENU</h2>
            
            <div class="grid grid-cols-2 gap-3">
                <button onclick="showSection('sec-download')" class="border border-[#00ff9d]/50 p-4 hover:bg-[#00ff9d]/10 transition text-center group">
                    <i class="fa-solid fa-download text-2xl mb-2 group-hover:scale-110 transition"></i>
                    <p class="text-xs font-bold">DOWNLOADER</p>
                </button>
                <button onclick="showSection('sec-booster')" class="border border-[#00ff9d]/50 p-4 hover:bg-[#00ff9d]/10 transition text-center group">
                    <i class="fa-solid fa-rocket text-2xl mb-2 group-hover:scale-110 transition text-pink-500"></i>
                    <p class="text-xs font-bold text-pink-500">VIEW BOOSTER</p>
                </button>
                <button onclick="showSection('sec-premium')" class="col-span-2 border border-yellow-500/50 p-3 hover:bg-yellow-500/10 transition text-center group">
                    <i class="fa-solid fa-crown text-yellow-500"></i>
                    <span class="text-xs font-bold text-yellow-500 ml-2">BUY PREMIUM ACCESS</span>
                </button>
            </div>
        </div>

        <!-- SECTION: DOWNLOADER -->
        <div id="sec-download" class="glass-box p-6 hidden relative">
            <button onclick="showSection('main')" class="absolute top-2 right-2 text-xs text-gray-500">[X]</button>
            <h3 class="font-bold mb-4 text-[#00ff9d]">>> VIDEO EXTRACTOR</h3>
            <input type="text" id="dlUrl" placeholder="PASTE LINK..." class="w-full input-cyber p-3 mb-3 text-sm">
            <button onclick="fetchVideo()" id="dlBtn" class="w-full border border-[#00ff9d] text-[#00ff9d] p-2 hover:bg-[#00ff9d] hover:text-black transition font-bold text-sm">EXTRACT DATA</button>
            
            <div id="dlResult" class="hidden mt-4 border-t border-gray-800 pt-4">
                <!-- Result here -->
            </div>
        </div>

        <!-- SECTION: VIEW BOOSTER (THE MAIN FEATURE) -->
        <div id="sec-booster" class="glass-box p-6 hidden relative">
            <button onclick="showSection('main')" class="absolute top-2 right-2 text-xs text-gray-500">[X]</button>
            <h3 class="font-bold mb-2 text-pink-500">>> 1000 VIEWS INJECTOR</h3>
            <p class="text-[10px] text-gray-400 mb-4">STATUS: <span class="text-green-500">ONLINE</span> | SPEED: <span class="text-red-500">TURBO</span></p>

            <input type="text" id="boostUrl" placeholder="VIDEO URL FOR VIEWS..." class="w-full input-cyber p-3 mb-3 text-sm border-pink-500/50 focus:border-pink-500">
            
            <div id="consoleBox" class="console-log hidden mb-3"></div>
            
            <div id="progressArea" class="hidden mb-3">
                <div class="flex justify-between text-[10px] mb-1">
                    <span>INJECTING VIEWS...</span>
                    <span id="viewCount">0 / 1000</span>
                </div>
                <div class="progress-container">
                    <div id="boostBar" class="progress-bar"></div>
                </div>
            </div>

            <button onclick="startBoost()" id="boostBtn" class="w-full bg-pink-600 text-white p-3 font-bold text-sm hover:bg-pink-700 transition shadow-[0_0_15px_rgba(236,72,153,0.5)]">
                INITIATE ATTACK (1000 VIEWS)
            </button>
        </div>

        <!-- SECTION: PREMIUM -->
        <div id="sec-premium" class="glass-box p-6 hidden relative border-yellow-500/30">
            <button onclick="showSection('main')" class="absolute top-2 right-2 text-xs text-gray-500">[X]</button>
            <div class="text-center">
                <i class="fa-solid fa-gem text-4xl text-yellow-400 mb-2 animate-bounce"></i>
                <h3 class="text-xl font-bold text-white">LIFETIME ACCESS</h3>
                <p class="text-xs text-gray-400 mb-4">Unlimited Views + API Access</p>
                
                <div class="bg-black/50 p-4 border border-yellow-500/20 mb-4">
                    <p class="text-sm text-gray-400">JAZZCASH NUMBER:</p>
                    <p class="text-2xl font-mono font-bold text-yellow-400 tracking-wider">03076485827</p>
                    <p class="text-xs mt-2 text-green-400">PRICE: RS. 150 ONLY</p>
                </div>

                <input type="text" placeholder="SENDER NUMBER" class="w-full input-cyber p-2 mb-2 text-xs">
                <input type="text" placeholder="TRX ID" class="w-full input-cyber p-2 mb-3 text-xs">
                <button onclick="alert('Request Sent to Admin! Wait for approval.')" class="w-full bg-yellow-600 text-black font-bold p-2 hover:bg-yellow-500">SUBMIT</button>
            </div>
        </div>

    </div>

    <script>
        // --- AUTH LOGIC (LocalStorage Mock DB) ---
        function checkLogin() {
            const user = localStorage.getItem('tiktokUser');
            if (user) {
                document.getElementById('authScreen').classList.add('hidden');
                document.getElementById('dashboard').classList.remove('hidden');
                document.getElementById('displayUser').innerText = user.toUpperCase();
            }
        }
        checkLogin();

        function toggleAuth() {
            document.getElementById('loginForm').classList.toggle('hidden');
            document.getElementById('signupForm').classList.toggle('hidden');
        }

        function handleSignup() {
            const u = document.getElementById('s_user').value;
            const p = document.getElementById('s_pass').value;
            if(!u || !p) return alert("ENTER CREDENTIALS");
            
            localStorage.setItem('tiktokUser', u);
            localStorage.setItem('tiktokPass', p);
            alert("REGISTRATION SUCCESSFUL. PLEASE LOGIN.");
            toggleAuth();
        }

        function handleLogin() {
            const u = document.getElementById('l_user').value;
            const p = document.getElementById('l_pass').value;
            const savedU = localStorage.getItem('tiktokUser');
            const savedP = localStorage.getItem('tiktokPass');

            if(u === savedU && p === savedP) {
                checkLogin();
            } else {
                alert("ACCESS DENIED: WRONG CREDENTIALS");
            }
        }

        function logout() {
            localStorage.removeItem('tiktokUser'); // Note: For this demo we logout fully
            location.reload();
        }

        // --- DASHBOARD NAVIGATION ---
        function showSection(id) {
            document.getElementById('sec-download').classList.add('hidden');
            document.getElementById('sec-booster').classList.add('hidden');
            document.getElementById('sec-premium').classList.add('hidden');
            
            if(id !== 'main') {
                document.getElementById(id).classList.remove('hidden');
            }
        }

        // --- 1000 VIEWS BOOSTER LOGIC (Simulation) ---
        function startBoost() {
            const url = document.getElementById('boostUrl').value;
            if(!url) return alert("NO TARGET DETECTED");

            const btn = document.getElementById('boostBtn');
            const consoleBox = document.getElementById('consoleBox');
            const progressArea = document.getElementById('progressArea');
            const bar = document.getElementById('boostBar');
            const count = document.getElementById('viewCount');

            btn.disabled = true;
            btn.classList.add('opacity-50');
            consoleBox.classList.remove('hidden');
            progressArea.classList.remove('hidden');
            consoleBox.innerHTML = "> CONNECTING TO SERVER...<br>";

            let progress = 0;
            let views = 0;
            
            // This interval runs for exactly 60 seconds approx (simulated)
            const interval = setInterval(() => {
                progress += 1.6; // Increment progress
                views += 17; // Increment views
                
                if (progress > 100) progress = 100;
                if (views > 1000) views = 1000;

                bar.style.width = progress + "%";
                count.innerText = Math.floor(views) + " / 1000";

                // Add random logs
                if(Math.random() > 0.7) {
                    const logs = [
                        "> PACKET SENT [OK]", 
                        "> BYPASSING FIREWALL...", 
                        "> INJECTING 50 VIEWS...", 
                        "> SERVER RESPONSE: 200 OK"
                    ];
                    consoleBox.innerHTML += logs[Math.floor(Math.random() * logs.length)] + "<br>";
                    consoleBox.scrollTop = consoleBox.scrollHeight;
                }

                if (views >= 1000) {
                    clearInterval(interval);
                    consoleBox.innerHTML += "> <span style='color:#00ff9d'>TASK COMPLETED SUCCESSFULLY.</span>";
                    btn.disabled = false;
                    btn.classList.remove('opacity-50');
                    btn.innerText = "SEND MORE VIEWS";
                    alert("SUCCESS: 1000 VIEWS DELIVERED!");
                }
            }, 1000); // Updates every second for 60 seconds
        }

        // --- DOWNLOADER LOGIC ---
        async function fetchVideo() {
            const url = document.getElementById('dlUrl').value;
            const btn = document.getElementById('dlBtn');
            const resDiv = document.getElementById('dlResult');

            if(!url) return;
            btn.innerText = "PROCESSING...";
            
            try {
                const req = await fetch('/api/info', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url})
                });
                const data = await req.json();
                
                if(data.status === 'success') {
                    resDiv.innerHTML = `
                        <div class="flex gap-3 mb-2">
                            <img src="${data.cover}" class="w-16 h-20 object-cover border border-[#00ff9d]">
                            <div>
                                <p class="text-xs font-bold line-clamp-2">${data.title}</p>
                                <p class="text-[10px] text-gray-500 mt-1">@${data.author_name}</p>
                            </div>
                        </div>
                        <a href="/proxy_download?url=${encodeURIComponent(data.play_url)}&name=${data.id}&type=mp4" class="block w-full bg-[#00ff9d] text-black text-center text-xs font-bold py-2 hover:bg-white transition">DOWNLOAD VIDEO</a>
                    `;
                    resDiv.classList.remove('hidden');
                } else {
                    alert("ERROR: INVALID LINK");
                }
            } catch(e) {
                alert("SERVER ERROR");
            } finally {
                btn.innerText = "EXTRACT DATA";
            }
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

@app.route('/proxy_download')
def proxy_download():
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
