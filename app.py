from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import requests
import random

app = Flask(__name__)

# --- BACKEND LOGIC ---
def get_video_data(url):
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
                # Hum images ko direct nahi bhejenge, balky apny proxy route k zariye bhejenge
                "cover": d.get("cover"), 
                "author_avatar": d.get("author", {}).get("avatar"),
                "play_url": d.get("play"),
                "music_url": d.get("music"),
                "author_name": d.get("author", {}).get("nickname"),
                "stats": {
                    "views": d.get("play_count", 0),
                    "likes": d.get("digg_count", 0),
                    "downloads": d.get("download_count", 0)
                }
            }
        return {"status": "error"}
    except:
        return {"status": "error"}

# --- FRONTEND (VIRAL THEME) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>TikTak - Viral Downloader</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <meta name="referrer" content="no-referrer">
    
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&display=swap');
        
        body {
            font-family: 'Space Grotesk', sans-serif;
            background-color: #000;
            background-image: 
                radial-gradient(circle at 20% 30%, rgba(37, 244, 238, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 80% 70%, rgba(254, 44, 85, 0.15) 0%, transparent 40%);
            color: white;
            min-height: 100vh;
            overflow-x: hidden;
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        .neon-border {
            position: relative;
        }
        .neon-border::after {
            content: ''; position: absolute; bottom: -2px; left: 0; width: 100%; height: 2px;
            background: linear-gradient(90deg, #25F4EE, #FE2C55);
            box-shadow: 0 0 10px #FE2C55;
        }

        .btn-download {
            background: linear-gradient(90deg, #FE2C55, #FF0055);
            box-shadow: 0 0 15px rgba(254, 44, 85, 0.4);
            transition: transform 0.2s;
        }
        .btn-download:active { transform: scale(0.95); }

        .btn-audio {
            background: linear-gradient(90deg, #25F4EE, #00C2BA);
            box-shadow: 0 0 15px rgba(37, 244, 238, 0.3);
            color: black;
        }

        /* Ticker Animation */
        .ticker-wrap {
            position: fixed; bottom: 0; width: 100%; overflow: hidden; height: 30px; background: rgba(0,0,0,0.8);
            border-top: 1px solid #333; z-index: 50;
        }
        .ticker { display: inline-block; white-space: nowrap; animation: ticker 20s infinite linear; }
        @keyframes ticker { 0% { transform: translate3d(100%, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }

        .loader {
            border: 3px solid #333; border-top: 3px solid #FE2C55; border-radius: 50%;
            width: 30px; height: 30px; animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="flex flex-col items-center p-4">

    <!-- Navbar -->
    <div class="w-full max-w-md flex justify-between items-center py-4 mb-8">
        <h1 class="text-3xl font-bold tracking-tighter">
            Tik<span class="text-[#FE2C55]">Tak</span><span class="text-[#25F4EE]">.</span>
        </h1>
        <div class="flex gap-3">
            <div class="bg-white/10 p-2 rounded-full"><i class="fa-solid fa-fire text-orange-500"></i></div>
            <div class="bg-white/10 p-2 rounded-full"><i class="fa-solid fa-bolt text-yellow-400"></i></div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="w-full max-w-md">
        
        <!-- Hero Section -->
        <div class="text-center mb-8">
            <h2 class="text-xl font-bold mb-2">Save Videos in <span class="text-[#25F4EE]">Flash Speed</span></h2>
            <p class="text-xs text-gray-400">No Watermark • HD Quality • MP3 Audio</p>
        </div>

        <!-- Input Box -->
        <div class="glass-card p-2 rounded-2xl flex items-center mb-6 relative group">
            <div class="absolute -inset-0.5 bg-gradient-to-r from-[#25F4EE] to-[#FE2C55] rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-500"></div>
            <div class="relative flex-1 bg-black rounded-xl flex items-center overflow-hidden">
                <i class="fa-solid fa-link text-gray-500 pl-4"></i>
                <input type="text" id="urlInput" placeholder="Paste TikTok Link..." 
                    class="w-full bg-transparent p-4 outline-none text-white text-sm placeholder-gray-600">
            </div>
            <button onclick="paste()" class="relative ml-2 bg-[#1a1a1a] text-white p-3 rounded-xl hover:bg-[#333]">
                <i class="fa-regular fa-paste"></i>
            </button>
        </div>

        <button onclick="fetchInfo()" id="mainBtn" class="w-full btn-download py-4 rounded-xl font-bold text-lg tracking-wide mb-8 flex items-center justify-center gap-2">
            <span>DOWNLOAD NOW</span>
            <i class="fa-solid fa-cloud-arrow-down"></i>
        </button>

        <!-- Loading -->
        <div id="loading" class="hidden flex justify-center my-4">
            <div class="loader"></div>
        </div>

        <!-- RESULT AREA -->
        <div id="result" class="hidden animate-fade-in pb-20">
            
            <!-- Video Card -->
            <div class="glass-card rounded-2xl overflow-hidden mb-6">
                <!-- Image Fix: Using Proxy -->
                <div class="relative h-64 bg-gray-900">
                    <img id="thumb" src="" class="w-full h-full object-cover opacity-80">
                    <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>
                    
                    <div class="absolute bottom-4 left-4 right-4">
                        <div class="flex items-center gap-2 mb-2">
                            <img id="avatar" src="" class="w-8 h-8 rounded-full border border-white">
                            <span id="author" class="text-sm font-bold text-white shadow-black drop-shadow-md">User</span>
                        </div>
                        <p id="title" class="text-xs text-gray-200 line-clamp-2">Title goes here...</p>
                    </div>
                </div>

                <!-- Stats Grid -->
                <div class="grid grid-cols-3 border-t border-white/10 divide-x divide-white/10 bg-black/40 backdrop-blur">
                    <div class="p-3 text-center">
                        <p class="text-[10px] text-gray-400">VIEWS</p>
                        <p id="views" class="font-bold text-sm">0</p>
                    </div>
                    <div class="p-3 text-center">
                        <p class="text-[10px] text-gray-400">LIKES</p>
                        <p id="likes" class="font-bold text-sm">0</p>
                    </div>
                    <div class="p-3 text-center">
                        <p class="text-[10px] text-gray-400">SAVES</p>
                        <p id="downloads" class="font-bold text-sm">0</p>
                    </div>
                </div>
            </div>

            <!-- Download Actions -->
            <div class="space-y-3">
                <a id="dlVideo" href="#" class="block w-full btn-download py-3.5 rounded-xl text-center font-bold text-sm">
                    <i class="fa-solid fa-video mr-2"></i> SAVE VIDEO (HD)
                </a>
                <a id="dlAudio" href="#" class="block w-full btn-audio py-3.5 rounded-xl text-center font-bold text-sm">
                    <i class="fa-solid fa-music mr-2"></i> EXTRACT AUDIO
                </a>
                <button onclick="location.reload()" class="block w-full bg-gray-800 text-gray-400 py-3 rounded-xl text-center text-xs">
                    Download Another
                </button>
            </div>

        </div>

        <!-- ERROR MESSAGE -->
        <div id="errorMsg" class="hidden bg-red-500/20 text-red-200 p-4 rounded-xl text-center text-sm border border-red-500/50">
            Video not found. Please check the link.
        </div>

    </div>

    <!-- Live Ticker -->
    <div class="ticker-wrap">
        <div class="ticker text-xs text-gray-300 py-1.5 font-mono">
            🔥 User from Pakistan just downloaded "Funny Cat Video" • ⚡ User from Dubai saved "Cricket Highlights" • 🚀 450 People online now • 🎵 "Dil Dil Pakistan" Audio Extracted
        </div>
    </div>

    <script>
        async function paste() {
            try {
                const t = await navigator.clipboard.readText();
                document.getElementById('urlInput').value = t;
            } catch(e) {}
        }

        // Formatter
        const nF = new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" });

        async function fetchInfo() {
            const url = document.getElementById('urlInput').value.trim();
            if(!url) return alert("Please enter link!");

            // UI Reset
            const btn = document.getElementById('mainBtn');
            const loader = document.getElementById('loading');
            const result = document.getElementById('result');
            const error = document.getElementById('errorMsg');

            btn.classList.add('hidden');
            loader.classList.remove('hidden');
            result.classList.add('hidden');
            error.classList.add('hidden');

            try {
                const res = await fetch('/api/info', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url})
                });
                const data = await res.json();

                if(data.status === 'success') {
                    // IMAGE FIX: Use Local Proxy
                    document.getElementById('thumb').src = `/proxy_image?url=${encodeURIComponent(data.cover)}`;
                    document.getElementById('avatar').src = `/proxy_image?url=${encodeURIComponent(data.author_avatar)}`;
                    
                    document.getElementById('title').innerText = data.title || "TikTok Video";
                    document.getElementById('author').innerText = "@" + data.author_name;
                    
                    document.getElementById('views').innerText = nF.format(data.stats.views);
                    document.getElementById('likes').innerText = nF.format(data.stats.likes);
                    document.getElementById('downloads').innerText = nF.format(data.stats.downloads);

                    // Links
                    document.getElementById('dlVideo').href = `/proxy_download?url=${encodeURIComponent(data.play_url)}&name=${data.id}&type=mp4`;
                    document.getElementById('dlAudio').href = `/proxy_download?url=${encodeURIComponent(data.music_url)}&name=${data.id}&type=mp3`;

                    result.classList.remove('hidden');
                } else {
                    error.classList.remove('hidden');
                    btn.classList.remove('hidden');
                }
            } catch(e) {
                error.classList.remove('hidden');
                btn.classList.remove('hidden');
            } finally {
                loader.classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/info', methods=['POST'])
def api_info():
    data = request.json
    result = get_video_data(data.get('url'))
    return jsonify(result)

# --- IMAGE PROXY (THE FIX FOR BROKEN IMAGES) ---
@app.route('/proxy_image')
def proxy_image():
    url = request.args.get('url')
    if not url: return "", 404
    # Fix: Ensure url is complete
    if not url.startswith('http'): url = "https://www.tikwm.com" + url
    
    try:
        # Stream image to bypass referrer checks
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return Response(r.content, mimetype="image/jpeg")
    except:
        return "", 404

# --- VIDEO/AUDIO PROXY ---
@app.route('/proxy_download')
def proxy_download():
    url = request.args.get('url')
    name = request.args.get('name', 'TikTak_Video')
    type_ = request.args.get('type', 'mp4')
    if not url: return "No URL", 400
    if not url.startswith('http'): url = "https://www.tikwm.com" + url
    
    try:
        r = requests.get(url, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        ct = "video/mp4" if type_ == 'mp4' else "audio/mpeg"
        fname = f"{name}.{type_}"
        return Response(stream_with_context(r.iter_content(chunk_size=4096)), content_type=ct, headers={"Content-Disposition": f"attachment; filename={fname}"})
    except: return "Error", 500

if __name__ == '__main__':
    app.run()
