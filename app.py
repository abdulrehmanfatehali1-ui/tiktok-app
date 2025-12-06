from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import requests
import datetime

app = Flask(__name__)

# --- BACKEND INTELLIGENCE (Hacker Logic) ---
def get_tiktok_data(url):
    try:
        api_url = "https://www.tikwm.com/api/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        params = {"url": url, "count": 12, "cursor": 0, "web": 1, "hd": 1}
        
        resp = requests.get(api_url, params=params, headers=headers)
        data = resp.json()
        
        if data.get("code") == 0:
            d = data["data"]
            
            # Engagement Calculation
            views = d.get("play_count", 1)
            interactions = d.get("digg_count", 0) + d.get("comment_count", 0) + d.get("share_count", 0)
            engagement_rate = round((interactions / views) * 100, 2)
            
            return {
                "status": "success",
                "id": d.get("id"),
                "title": d.get("title", "No Title"),
                "cover": d.get("cover"),
                "origin_cover": d.get("origin_cover", d.get("cover")),
                "play_url": d.get("play"),      # No Watermark Video
                "music_url": d.get("music"),    # Audio
                "music_title": d.get("music_info", {}).get("title", "Original Sound"),
                "music_cover": d.get("music_info", {}).get("cover", ""),
                "author": {
                    "id": d.get("author", {}).get("id"),
                    "name": d.get("author", {}).get("nickname"),
                    "unique_id": d.get("author", {}).get("unique_id"),
                    "avatar": d.get("author", {}).get("avatar"),
                },
                "stats": {
                    "views": d.get("play_count", 0),
                    "likes": d.get("digg_count", 0),
                    "comments": d.get("comment_count", 0),
                    "shares": d.get("share_count", 0),
                    "downloads": d.get("download_count", 0),
                    "engagement": f"{engagement_rate}%"
                },
                "timestamp": d.get("create_time"), # Upload Time
                "region": d.get("region", "Unknown"),
                "raw_data": d # Full JSON for Hacker Mode
            }
        return {"status": "error"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# --- FRONTEND (TikTok UI) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>TikTok OSINT Tool</title>
    <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/512/3046/3046121.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Proxima+Nova:wght@400;600;700&display=swap');
        
        body {
            font-family: 'Segoe UI', sans-serif;
            background-color: #121212; /* TikTok Dark BG */
            color: white;
            padding-bottom: 80px;
        }

        .tiktok-card {
            background-color: #1e1e1e;
            border: 1px solid #2f2f2f;
            border-radius: 12px;
        }

        .btn-primary {
            background-color: #fe2c55; /* TikTok Red */
            color: white;
            font-weight: bold;
            transition: all 0.2s;
        }
        .btn-primary:hover { background-color: #e0274b; }

        .btn-secondary {
            background-color: #2f2f2f;
            color: white;
            font-weight: 600;
        }

        .stat-box {
            background: #252525;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }

        /* Hacker JSON Viewer */
        .json-viewer {
            background: #000;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            padding: 15px;
            border-radius: 8px;
            font-size: 10px;
            overflow-x: auto;
            border: 1px solid #333;
        }
        
        .loader {
            border: 3px solid #333;
            border-top: 3px solid #fe2c55;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="p-4 flex flex-col items-center">

    <!-- Header -->
    <div class="w-full max-w-md flex items-center justify-between mb-6">
        <div class="flex items-center gap-2">
            <i class="fa-brands fa-tiktok text-3xl text-white shadow-[2px_2px_0px_#fe2c55,-2px_-2px_0px_#25f4ee]"></i>
            <h1 class="text-xl font-bold">Tik<span class="text-[#fe2c55]">Tool</span></h1>
        </div>
        <div class="bg-[#2f2f2f] px-3 py-1 rounded-full text-xs font-semibold">
            v2.0 Hacker Edition
        </div>
    </div>

    <!-- Search Input -->
    <div class="w-full max-w-md mb-6 relative">
        <input type="text" id="urlInput" placeholder="Paste link to analyze..." 
            class="w-full bg-[#2f2f2f] text-white p-4 rounded-xl outline-none border border-transparent focus:border-[#fe2c55] transition text-sm pr-12">
        
        <button onclick="pasteLink()" class="absolute right-4 top-4 text-gray-400 hover:text-white">
            <i class="fa-regular fa-paste"></i>
        </button>
    </div>

    <button onclick="analyzeVideo()" id="analyzeBtn" class="w-full max-w-md btn-primary py-3.5 rounded-xl text-sm mb-6 flex items-center justify-center gap-2">
        <i class="fa-solid fa-magnifying-glass"></i> Analyze Video
    </button>

    <!-- LOADING -->
    <div id="loading" class="hidden flex flex-col items-center mt-4">
        <div class="loader mb-2"></div>
        <p class="text-xs text-gray-500">Decrypting Metadata...</p>
    </div>

    <!-- ERROR MSG -->
    <div id="errorMsg" class="hidden w-full max-w-md bg-red-900/20 text-red-500 p-3 rounded-lg text-center text-sm border border-red-900/50 mb-4"></div>

    <!-- RESULT CONTAINER -->
    <div id="resultArea" class="w-full max-w-md hidden animate-fade-in pb-10">

        <!-- 1. PROFILE & VIDEO CARD -->
        <div class="tiktok-card p-4 mb-4">
            <!-- Profile Info -->
            <div class="flex items-center gap-3 mb-3 border-b border-[#2f2f2f] pb-3">
                <img id="uAvatar" src="" class="w-10 h-10 rounded-full border border-[#2f2f2f]">
                <div>
                    <h3 id="uName" class="text-sm font-bold">Nickname</h3>
                    <p id="uId" class="text-xs text-gray-400">@unique_id</p>
                </div>
                <a id="dlProfile" href="#" target="_blank" class="ml-auto text-xs bg-[#2f2f2f] px-3 py-1.5 rounded-md hover:bg-white hover:text-black transition">
                    <i class="fa-solid fa-download"></i> DP
                </a>
            </div>

            <!-- Video Info -->
            <div class="flex gap-3">
                <div class="relative w-24 h-32 bg-black rounded-lg overflow-hidden flex-shrink-0 border border-[#2f2f2f]">
                    <img id="vCover" src="" class="w-full h-full object-cover">
                </div>
                <div class="flex-1 flex flex-col justify-between">
                    <p id="vTitle" class="text-xs text-gray-200 line-clamp-3 mb-2">Video Caption...</p>
                    
                    <div class="flex gap-2">
                        <a id="btnDlVideo" href="#" class="flex-1 btn-primary text-center py-2 rounded-lg text-xs">
                            <i class="fa-solid fa-video"></i> MP4
                        </a>
                        <a id="btnDlAudio" href="#" class="flex-1 btn-secondary text-center py-2 rounded-lg text-xs">
                            <i class="fa-solid fa-music"></i> MP3
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <!-- 2. ANALYTICS (STATS) -->
        <div class="grid grid-cols-3 gap-3 mb-4">
            <div class="stat-box">
                <i class="fa-solid fa-eye text-[#25f4ee] mb-1"></i>
                <p id="statViews" class="text-sm font-bold">0</p>
                <p class="text-[10px] text-gray-500">Views</p>
            </div>
            <div class="stat-box">
                <i class="fa-solid fa-heart text-[#fe2c55] mb-1"></i>
                <p id="statLikes" class="text-sm font-bold">0</p>
                <p class="text-[10px] text-gray-500">Likes</p>
            </div>
            <div class="stat-box border border-[#fe2c55]/30">
                <i class="fa-solid fa-chart-line text-yellow-400 mb-1"></i>
                <p id="statEngage" class="text-sm font-bold">0%</p>
                <p class="text-[10px] text-gray-500">Engagement</p>
            </div>
        </div>

        <!-- 3. TAG SPY (Hashtags) -->
        <div class="tiktok-card p-4 mb-4">
            <h3 class="text-xs font-bold text-gray-400 mb-2 uppercase"><i class="fa-solid fa-hashtag"></i> Detected Tags</h3>
            <div id="tagBox" class="flex flex-wrap gap-2 text-[11px]">
                <!-- Tags injected here -->
            </div>
        </div>

        <!-- 4. MUSIC INTEL -->
        <div class="tiktok-card p-4 mb-4 flex items-center gap-3">
            <img id="mCover" src="" class="w-10 h-10 rounded bg-[#2f2f2f]">
            <div class="flex-1 overflow-hidden">
                <p class="text-xs font-bold text-gray-400 uppercase">Music Used</p>
                <p id="mTitle" class="text-xs truncate text-white">Original Sound</p>
            </div>
            <a id="dlMusicCover" href="#" target="_blank" class="text-xs text-[#25f4ee]">
                <i class="fa-solid fa-image"></i> Cover
            </a>
        </div>

        <!-- 5. TIMESTAMP DECODER -->
        <div class="tiktok-card p-4 mb-4">
            <div class="flex justify-between items-center text-xs">
                <span class="text-gray-400"><i class="fa-regular fa-clock"></i> Uploaded:</span>
                <span id="uploadTime" class="font-mono text-white">Calculating...</span>
            </div>
            <div class="flex justify-between items-center text-xs mt-2">
                <span class="text-gray-400"><i class="fa-solid fa-earth-americas"></i> Region:</span>
                <span id="regionCode" class="font-mono text-white">--</span>
            </div>
        </div>

        <!-- 6. HACKER MODE (Raw JSON) -->
        <div class="mb-4">
            <button onclick="toggleJson()" class="w-full text-xs text-gray-500 hover:text-[#25f4ee] mb-2 text-right">
                <i class="fa-solid fa-terminal"></i> Toggle Developer Data
            </button>
            <div id="jsonBox" class="json-viewer hidden">
                Loading Raw Data...
            </div>
        </div>

    </div>

    <script>
        async function pasteLink() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('urlInput').value = text;
            } catch(e) { alert('Permission Denied'); }
        }

        function toggleJson() {
            document.getElementById('jsonBox').classList.toggle('hidden');
        }

        function formatNum(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
            return num;
        }

        // --- CORE ANALYSIS LOGIC ---
        async function analyzeVideo() {
            const url = document.getElementById('urlInput').value.trim();
            const btn = document.getElementById('analyzeBtn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('resultArea');
            const error = document.getElementById('errorMsg');

            if(!url) return;

            // UI Reset
            btn.disabled = true;
            btn.classList.add('opacity-50');
            loading.classList.remove('hidden');
            result.classList.add('hidden');
            error.classList.add('hidden');

            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url})
                });
                const data = await response.json();

                if(data.status === 'success') {
                    // 1. Profile Data
                    document.getElementById('uAvatar').src = `/proxy_image?url=${encodeURIComponent(data.author.avatar)}`;
                    document.getElementById('uName').innerText = data.author.name;
                    document.getElementById('uId').innerText = "@" + data.author.unique_id;
                    document.getElementById('dlProfile').href = `/proxy_download?url=${encodeURIComponent(data.author.avatar)}&name=profile_${data.author.unique_id}&type=jpeg`;

                    // 2. Video Data
                    document.getElementById('vCover').src = `/proxy_image?url=${encodeURIComponent(data.origin_cover)}`; // HD Cover
                    document.getElementById('vTitle').innerText = data.title;
                    
                    // 3. Stats & Engagement
                    document.getElementById('statViews').innerText = formatNum(data.stats.views);
                    document.getElementById('statLikes').innerText = formatNum(data.stats.likes);
                    document.getElementById('statEngage').innerText = data.stats.engagement;

                    // 4. Hashtag Extraction
                    const tags = data.title.match(/#[\w]+/g) || [];
                    const tagBox = document.getElementById('tagBox');
                    tagBox.innerHTML = tags.length > 0 
                        ? tags.map(t => `<span class="bg-[#2f2f2f] px-2 py-1 rounded text-[#25f4ee]">${t}</span>`).join('')
                        : '<span class="text-gray-600">No hashtags found.</span>';

                    // 5. Music Data
                    document.getElementById('mTitle').innerText = data.music_title;
                    document.getElementById('mCover').src = `/proxy_image?url=${encodeURIComponent(data.music_cover)}`;
                    document.getElementById('dlMusicCover').href = data.music_cover;

                    // 6. Timestamp & Region
                    if(data.timestamp) {
                        const date = new Date(data.timestamp * 1000);
                        document.getElementById('uploadTime').innerText = date.toLocaleString();
                    }
                    document.getElementById('regionCode').innerText = data.region.toUpperCase();

                    // 7. Raw JSON (Hacker Mode)
                    document.getElementById('jsonBox').textContent = JSON.stringify(data.raw_data, null, 2);

                    // Set Download Links
                    document.getElementById('btnDlVideo').href = `/proxy_download?url=${encodeURIComponent(data.play_url)}&name=${data.id}&type=mp4`;
                    document.getElementById('btnDlAudio').href = `/proxy_download?url=${encodeURIComponent(data.music_url)}&name=${data.id}&type=mp3`;

                    result.classList.remove('hidden');
                } else {
                    error.innerText = "Target not found. Check link security level.";
                    error.classList.remove('hidden');
                }

            } catch(e) {
                error.innerText = "System Failure. Connection refused.";
                error.classList.remove('hidden');
            } finally {
                loading.classList.add('hidden');
                btn.disabled = false;
                btn.classList.remove('opacity-50');
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

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.json
    result = get_tiktok_data(data.get('url'))
    return jsonify(result)

# --- PROXY ENGINE (For Images & Downloads) ---
@app.route('/proxy_image')
def proxy_image():
    url = request.args.get('url')
    if not url: return "", 404
    if not url.startswith('http'): url = "https://www.tikwm.com" + url
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return Response(r.content, mimetype="image/jpeg")
    except: return "", 404

@app.route('/proxy_download')
def proxy_download():
    url = request.args.get('url')
    name = request.args.get('name', 'file')
    type_ = request.args.get('type', 'mp4')
    if not url: return "No URL", 400
    if not url.startswith('http'): url = "https://www.tikwm.com" + url
    
    try:
        r = requests.get(url, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        ct = "video/mp4" if type_ == 'mp4' else "audio/mpeg"
        if type_ == 'jpeg': ct = "image/jpeg"
        
        fname = f"{name}.{type_}"
        return Response(stream_with_context(r.iter_content(chunk_size=4096)), content_type=ct, 
                       headers={"Content-Disposition": f"attachment; filename={fname}"})
    except: return "Error", 500

if __name__ == '__main__':
    app.run()
