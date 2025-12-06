from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import requests
import datetime
import math

app = Flask(__name__)

# --- BACKEND INTELLIGENCE ---
def get_video_data(url):
    try:
        api_url = "https://www.tikwm.com/api/"
        headers = {"User-Agent": "Mozilla/5.0"}
        params = {"url": url, "count": 12, "cursor": 0, "web": 1, "hd": 1}
        resp = requests.get(api_url, params=params, headers=headers)
        data = resp.json()
        
        if data.get("code") == 0:
            d = data["data"]
            
            # --- CALCULATIONS ---
            # 1. Engagement Rate
            views = d.get("play_count", 1)
            likes = d.get("digg_count", 0)
            shares = d.get("share_count", 0)
            comments = d.get("comment_count", 0)
            engagement = ((likes + comments + shares) / views) * 100
            
            # 2. Viral Score (0-100)
            viral_score = min(100, (views / 10000) * 5 + (engagement * 2))
            
            # 3. Time Parsing
            ts = d.get("create_time")
            dt = datetime.datetime.fromtimestamp(ts)
            
            return {
                "status": "success",
                # Media
                "id": d.get("id"),
                "play_url": d.get("play"), 
                "music_url": d.get("music"),
                "cover": d.get("origin_cover"),
                "dynamic_cover": d.get("cover"),
                # Author
                "author": {
                    "id": d.get("author", {}).get("unique_id"),
                    "name": d.get("author", {}).get("nickname"),
                    "avatar": d.get("author", {}).get("avatar"),
                    "signature": d.get("author", {}).get("signature", "No Bio"),
                },
                # Music
                "music": {
                    "title": d.get("music_info", {}).get("title"),
                    "author": d.get("music_info", {}).get("author"),
                    "cover": d.get("music_info", {}).get("cover"),
                    "duration": d.get("duration", 0)
                },
                # Stats
                "stats": {
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "downloads": d.get("download_count", 0),
                    "engagement": f"{engagement:.2f}%",
                    "viral_score": int(viral_score)
                },
                # Metadata
                "meta": {
                    "title": d.get("title", ""),
                    "region": d.get("region", "Global"),
                    "date": dt.strftime('%Y-%m-%d'),
                    "time": dt.strftime('%H:%M:%S'),
                    "duration": d.get("duration", 0)
                },
                # Raw (for QR)
                "share_url": url
            }
        return {"status": "error"}
    except:
        return {"status": "error"}

# --- UI TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>TikTokWala Ultimate</title>
    <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/512/3046/3046121.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <!-- QR Code Lib -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    <meta name="referrer" content="no-referrer"> 
    
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sofia+Sans:wght@300;500;700;900&display=swap');
        
        body { 
            font-family: 'Sofia Sans', sans-serif; 
            background-color: #121212; 
            color: #fff; 
            padding-bottom: 90px;
        }

        /* TikTok Colors */
        :root {
            --tk-cyan: #25F4EE;
            --tk-pink: #FE2C55;
            --bg-card: #1E1E1E;
        }

        /* Logo Animation */
        .glitch-wrapper { position: relative; display: inline-block; }
        .glitch-text { font-weight: 900; font-size: 24px; position: relative; color: white; }
        .glitch-text::before, .glitch-text::after {
            content: attr(data-text); position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        }
        .glitch-text::before { left: 2px; text-shadow: -1px 0 var(--tk-pink); clip: rect(24px, 550px, 90px, 0); animation: glitch-anim 3s infinite linear alternate-reverse; }
        .glitch-text::after { left: -2px; text-shadow: -1px 0 var(--tk-cyan); clip: rect(85px, 550px, 140px, 0); animation: glitch-anim 2.5s infinite linear alternate-reverse; }
        @keyframes glitch-anim {
            0% { clip: rect(10px, 9999px, 30px, 0); }
            20% { clip: rect(30px, 9999px, 80px, 0); }
            40% { clip: rect(80px, 9999px, 10px, 0); }
            100% { clip: rect(50px, 9999px, 90px, 0); }
        }

        .card { background: var(--bg-card); border-radius: 12px; border: 1px solid #2f2f2f; }
        .input-box { background: #2F2F2F; border: none; color: white; outline: none; transition: 0.3s; }
        .input-box:focus { box-shadow: 0 0 0 2px var(--tk-pink); }
        
        .btn-main {
            background: var(--tk-pink); color: white; font-weight: bold;
            transition: 0.2s; border-radius: 8px;
        }
        .btn-main:active { transform: scale(0.98); }

        .stat-item { text-align: center; padding: 10px; background: #252525; border-radius: 8px; }
        
        /* Bottom Nav */
        .bottom-nav {
            position: fixed; bottom: 0; left: 0; width: 100%;
            background: #000; border-top: 1px solid #333;
            display: flex; justify-content: space-around; padding: 12px; z-index: 50;
        }
        .nav-icon { color: #666; font-size: 20px; transition: 0.3s; }
        .nav-icon.active { color: white; transform: translateY(-5px); }

        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.3s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .tag { background: #333; padding: 2px 8px; border-radius: 4px; font-size: 11px; color: var(--tk-cyan); }
    </style>
</head>
<body class="p-4 flex flex-col items-center">

    <!-- HEADER -->
    <div class="w-full max-w-md flex justify-between items-center mb-6">
        <div class="glitch-wrapper">
            <div class="glitch-text" data-text="TikTokWala">TikTokWala</div>
        </div>
        <div class="text-xs font-mono text-gray-400 bg-gray-800 px-2 py-1 rounded">ULTRA v3.0</div>
    </div>

    <!-- TABS CONTENT CONTAINER -->
    <div class="w-full max-w-md">

        <!-- ============ TAB 1: HOME (DOWNLOADER) ============ -->
        <div id="tab-home" class="tab-content active">
            
            <!-- Search -->
            <div class="relative mb-6">
                <input type="text" id="urlInput" placeholder="Paste link here..." class="w-full input-box p-4 pr-12 rounded-xl text-sm">
                <button onclick="pasteLink()" class="absolute right-4 top-4 text-gray-400 hover:text-white">
                    <i class="fa-solid fa-clipboard"></i>
                </button>
            </div>
            
            <button onclick="analyze()" id="mainBtn" class="w-full btn-main py-4 text-sm tracking-wide shadow-[0_4px_15px_rgba(254,44,85,0.4)]">
                GET DATA <i class="fa-solid fa-bolt ml-1"></i>
            </button>

            <!-- Loading -->
            <div id="loading" class="hidden flex justify-center py-6">
                <i class="fa-solid fa-circle-notch fa-spin text-2xl text-[#fe2c55]"></i>
            </div>

            <!-- RESULT CARD -->
            <div id="result" class="hidden mt-6 animate-fade-in">
                
                <!-- Video Player Preview -->
                <div class="card p-2 mb-4 relative">
                    <video id="vidPreview" controls class="w-full rounded-lg bg-black max-h-[400px]" poster=""></video>
                    <div id="viralBadge" class="absolute top-4 right-4 bg-yellow-500 text-black text-xs font-bold px-2 py-1 rounded hidden">
                        <i class="fa-solid fa-fire"></i> TRENDING
                    </div>
                </div>

                <!-- Main Info -->
                <div class="flex items-start justify-between mb-4">
                    <div>
                        <h2 id="vTitle" class="font-bold text-sm line-clamp-2 mb-1">Title</h2>
                        <div class="flex items-center gap-2">
                            <img id="uAvatar" src="" class="w-5 h-5 rounded-full">
                            <span id="uName" class="text-xs text-gray-400">User</span>
                            <span id="vRegion" class="text-[10px] bg-gray-800 px-1 rounded text-gray-500">US</span>
                        </div>
                    </div>
                    <button onclick="downloadAsset('profile')" class="text-xs bg-gray-800 px-2 py-1 rounded hover:bg-gray-700">
                        <i class="fa-solid fa-user"></i> DP
                    </button>
                </div>

                <!-- 4 Major Actions -->
                <div class="grid grid-cols-2 gap-3 mb-6">
                    <a id="dlVideo" href="#" class="btn-main py-2 text-center text-xs flex items-center justify-center gap-2">
                        <i class="fa-solid fa-video"></i> No Watermark
                    </a>
                    <a id="dlAudio" href="#" class="bg-gray-700 text-white py-2 rounded-lg text-center text-xs flex items-center justify-center gap-2">
                        <i class="fa-solid fa-music"></i> Save Audio
                    </a>
                    <button onclick="downloadAsset('cover')" class="bg-gray-800 py-2 rounded-lg text-xs">
                        <i class="fa-solid fa-image"></i> HD Cover
                    </button>
                    <button onclick="downloadAsset('dynamic')" class="bg-gray-800 py-2 rounded-lg text-xs">
                        <i class="fa-solid fa-film"></i> GIF Cover
                    </button>
                </div>

                <!-- Music Player -->
                <div class="card p-3 flex items-center gap-3 mb-6">
                    <img id="mCover" class="w-10 h-10 rounded bg-gray-800">
                    <div class="flex-1 overflow-hidden">
                        <p id="mTitle" class="text-xs font-bold truncate">Sound</p>
                        <p id="mAuthor" class="text-[10px] text-gray-400">Artist</p>
                    </div>
                    <audio id="audioPreview" controls class="h-8 w-24"></audio>
                </div>

            </div>
        </div>

        <!-- ============ TAB 2: ANALYTICS (DATA) ============ -->
        <div id="tab-stats" class="tab-content">
            <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
                <i class="fa-solid fa-chart-pie text-[#25f4ee]"></i> Deep Analytics
            </h2>

            <div id="statsContent" class="hidden">
                <!-- Score Board -->
                <div class="card p-4 mb-4 flex justify-between items-center bg-gradient-to-r from-gray-900 to-gray-800">
                    <div>
                        <p class="text-xs text-gray-500">VIRAL SCORE</p>
                        <h3 id="viralScore" class="text-3xl font-black text-[#25f4ee]">0</h3>
                    </div>
                    <div class="text-right">
                        <p class="text-xs text-gray-500">ENGAGEMENT</p>
                        <h3 id="engRate" class="text-xl font-bold text-white">0%</h3>
                    </div>
                </div>

                <!-- Detailed Grid -->
                <div class="grid grid-cols-3 gap-2 mb-4">
                    <div class="stat-item">
                        <i class="fa-solid fa-eye text-gray-400 mb-1"></i>
                        <p id="sViews" class="text-sm font-bold">0</p>
                        <p class="text-[10px] text-gray-500">Views</p>
                    </div>
                    <div class="stat-item">
                        <i class="fa-solid fa-heart text-[#fe2c55] mb-1"></i>
                        <p id="sLikes" class="text-sm font-bold">0</p>
                        <p class="text-[10px] text-gray-500">Likes</p>
                    </div>
                    <div class="stat-item">
                        <i class="fa-solid fa-share text-blue-400 mb-1"></i>
                        <p id="sShares" class="text-sm font-bold">0</p>
                        <p class="text-[10px] text-gray-500">Shares</p>
                    </div>
                    <div class="stat-item">
                        <i class="fa-solid fa-comment text-green-400 mb-1"></i>
                        <p id="sComments" class="text-sm font-bold">0</p>
                        <p class="text-[10px] text-gray-500">Comments</p>
                    </div>
                    <div class="stat-item">
                        <i class="fa-solid fa-download text-yellow-400 mb-1"></i>
                        <p id="sDownloads" class="text-sm font-bold">0</p>
                        <p class="text-[10px] text-gray-500">Saves</p>
                    </div>
                    <div class="stat-item">
                        <i class="fa-regular fa-clock text-purple-400 mb-1"></i>
                        <p id="sDuration" class="text-sm font-bold">0s</p>
                        <p class="text-[10px] text-gray-500">Length</p>
                    </div>
                </div>

                <!-- Time Details -->
                <div class="card p-4">
                    <div class="flex justify-between border-b border-gray-700 pb-2 mb-2">
                        <span class="text-xs text-gray-400">Upload Date</span>
                        <span id="sDate" class="text-xs font-mono">--</span>
                    </div>
                    <div class="flex justify-between border-b border-gray-700 pb-2 mb-2">
                        <span class="text-xs text-gray-400">Upload Time</span>
                        <span id="sTime" class="text-xs font-mono">--</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-xs text-gray-400">Video ID</span>
                        <span id="sVidId" class="text-[10px] font-mono">--</span>
                    </div>
                </div>
            </div>
            
            <div id="statsEmpty" class="text-center text-gray-500 py-10 text-xs">
                Search a video first to see data.
            </div>
        </div>

        <!-- ============ TAB 3: TOOLS (SEO) ============ -->
        <div id="tab-tools" class="tab-content">
            <h2 class="text-lg font-bold mb-4 flex items-center gap-2">
                <i class="fa-solid fa-toolbox text-yellow-500"></i> Smart Tools
            </h2>
            
            <div id="toolsContent" class="hidden space-y-4">
                
                <!-- Tool 1: Caption -->
                <div class="card p-4">
                    <div class="flex justify-between mb-2">
                        <h3 class="text-xs font-bold text-gray-400">CAPTION ANALYSIS</h3>
                        <button onclick="copyText('fullCaption')" class="text-xs text-[#25f4ee]">Copy</button>
                    </div>
                    <p id="fullCaption" class="text-xs text-gray-300 leading-relaxed mb-3">...</p>
                    
                    <div class="bg-black p-2 rounded flex items-center gap-2">
                        <span class="text-[10px] text-gray-500">SENTIMENT:</span>
                        <span id="sentimentBadge" class="text-[10px] font-bold px-2 py-0.5 rounded bg-gray-700">--</span>
                    </div>
                </div>

                <!-- Tool 2: Tags -->
                <div class="card p-4">
                    <div class="flex justify-between mb-2">
                        <h3 class="text-xs font-bold text-gray-400">HASHTAGS <span id="tagCount" class="text-[10px] bg-gray-700 px-1 rounded">0</span></h3>
                        <button onclick="copyTags()" class="text-xs text-[#25f4ee]">Copy All</button>
                    </div>
                    <div id="tagContainer" class="flex flex-wrap gap-2"></div>
                </div>

                <!-- Tool 3: QR Code -->
                <div class="card p-4 flex flex-col items-center">
                    <h3 class="text-xs font-bold text-gray-400 mb-3">SHARE QR CODE</h3>
                    <div id="qrcode" class="p-2 bg-white rounded"></div>
                    <button onclick="shareWhatsapp()" class="mt-4 w-full bg-green-600 py-2 rounded text-xs font-bold">
                        <i class="fa-brands fa-whatsapp"></i> Share Link
                    </button>
                </div>

            </div>
            
            <div id="toolsEmpty" class="text-center text-gray-500 py-10 text-xs">
                Search a video first to use tools.
            </div>
        </div>

        <!-- ============ TAB 4: HISTORY ============ -->
        <div id="tab-history" class="tab-content">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-lg font-bold">History</h2>
                <button onclick="clearHistory()" class="text-xs text-red-500">Clear All</button>
            </div>
            <div id="historyList" class="space-y-3"></div>
        </div>

    </div>

    <!-- BOTTOM NAV -->
    <div class="bottom-nav">
        <i onclick="switchTab('tab-home', this)" class="fa-solid fa-house nav-icon active"></i>
        <i onclick="switchTab('tab-stats', this)" class="fa-solid fa-chart-simple nav-icon"></i>
        <i onclick="switchTab('tab-tools', this)" class="fa-solid fa-briefcase nav-icon"></i>
        <i onclick="switchTab('tab-history', this)" class="fa-solid fa-clock-rotate-left nav-icon"></i>
    </div>

    <script>
        let currentData = null;

        // --- CORE LOGIC ---
        function switchTab(id, el) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            document.querySelectorAll('.nav-icon').forEach(i => i.classList.remove('active'));
            el.classList.add('active');
        }

        async function pasteLink() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('urlInput').value = text;
            } catch(e) {}
        }

        function copyText(id) {
            const txt = document.getElementById(id).innerText;
            navigator.clipboard.writeText(txt);
            alert("Copied!");
        }

        function copyTags() {
            if(!currentData) return;
            const tags = currentData.meta.title.match(/#[\w]+/g) || [];
            navigator.clipboard.writeText(tags.join(' '));
            alert("Tags Copied!");
        }

        function formatNum(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
            return num;
        }

        function shareWhatsapp() {
            if(!currentData) return;
            window.open(`https://wa.me/?text=Check this video: ${currentData.share_url}`, '_blank');
        }

        // --- MAIN ANALYZER ---
        async function analyze() {
            const url = document.getElementById('urlInput').value.trim();
            if(!url) return alert("Please enter a link!");

            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('result').classList.add('hidden');
            
            try {
                const req = await fetch('/api/info', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url})
                });
                const data = await req.json();
                currentData = data;

                if(data.status === 'success') {
                    // 1. POPULATE HOME
                    document.getElementById('vTitle').innerText = data.meta.title || "No Title";
                    document.getElementById('uName').innerText = data.author.name;
                    document.getElementById('uAvatar').src = `/proxy_image?url=${encodeURIComponent(data.author.avatar)}`;
                    document.getElementById('vRegion').innerText = data.meta.region.toUpperCase();
                    
                    document.getElementById('vidPreview').src = `/proxy_download?url=${encodeURIComponent(data.play_url)}&name=${data.id}&type=mp4`;
                    document.getElementById('vidPreview').poster = `/proxy_image?url=${encodeURIComponent(data.cover)}`;

                    document.getElementById('mTitle').innerText = data.music.title;
                    document.getElementById('mAuthor').innerText = data.music.author;
                    document.getElementById('mCover').src = `/proxy_image?url=${encodeURIComponent(data.music.cover)}`;
                    document.getElementById('audioPreview').src = `/proxy_download?url=${encodeURIComponent(data.music_url)}&name=${data.id}&type=mp3`;

                    // Links
                    document.getElementById('dlVideo').href = `/proxy_download?url=${encodeURIComponent(data.play_url)}&name=${data.id}&type=mp4`;
                    document.getElementById('dlAudio').href = `/proxy_download?url=${encodeURIComponent(data.music_url)}&name=${data.id}&type=mp3`;

                    // Badge
                    if(data.stats.viral_score > 70) {
                        document.getElementById('viralBadge').classList.remove('hidden');
                    } else {
                        document.getElementById('viralBadge').classList.add('hidden');
                    }

                    // 2. POPULATE STATS
                    document.getElementById('sViews').innerText = formatNum(data.stats.views);
                    document.getElementById('sLikes').innerText = formatNum(data.stats.likes);
                    document.getElementById('sShares').innerText = formatNum(data.stats.shares);
                    document.getElementById('sComments').innerText = formatNum(data.stats.comments);
                    document.getElementById('sDownloads').innerText = formatNum(data.stats.downloads);
                    document.getElementById('sDuration').innerText = data.meta.duration + "s";
                    
                    document.getElementById('viralScore').innerText = data.stats.viral_score;
                    document.getElementById('engRate').innerText = data.stats.engagement;
                    
                    document.getElementById('sDate').innerText = data.meta.date;
                    document.getElementById('sTime').innerText = data.meta.time;
                    document.getElementById('sVidId').innerText = data.id;

                    document.getElementById('statsContent').classList.remove('hidden');
                    document.getElementById('statsEmpty').classList.add('hidden');

                    // 3. POPULATE TOOLS
                    document.getElementById('fullCaption').innerText = data.meta.title;
                    
                    // Basic Sentiment
                    const titleLower = data.meta.title.toLowerCase();
                    let mood = "Neutral";
                    if(titleLower.includes('sad') || titleLower.includes('cry') || titleLower.includes('miss')) mood = "Sad 😔";
                    else if(titleLower.includes('happy') || titleLower.includes('fun') || titleLower.includes('love')) mood = "Happy 😊";
                    else if(titleLower.includes('lol') || titleLower.includes('funny')) mood = "Funny 😂";
                    
                    const badge = document.getElementById('sentimentBadge');
                    badge.innerText = mood;
                    badge.className = "text-[10px] font-bold px-2 py-0.5 rounded " + (mood.includes('Sad') ? "bg-blue-900 text-blue-300" : mood.includes('Happy') ? "bg-green-900 text-green-300" : "bg-gray-700");

                    // Hashtags
                    const tags = data.meta.title.match(/#[\w]+/g) || [];
                    document.getElementById('tagCount').innerText = tags.length;
                    document.getElementById('tagContainer').innerHTML = tags.length ? 
                        tags.map(t => `<span class="tag">${t}</span>`).join('') : 
                        '<span class="text-xs text-gray-600">No tags</span>';

                    // QR Code
                    document.getElementById('qrcode').innerHTML = "";
                    new QRCode(document.getElementById("qrcode"), {
                        text: data.share_url,
                        width: 100,
                        height: 100
                    });

                    document.getElementById('toolsContent').classList.remove('hidden');
                    document.getElementById('toolsEmpty').classList.add('hidden');

                    // 4. HISTORY
                    addToHistory(data);

                    document.getElementById('result').classList.remove('hidden');
                } else {
                    alert("Not Found");
                }
            } catch(e) {
                console.error(e);
                alert("Error");
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        }

        // --- ASSET DOWNLOADER ---
        function downloadAsset(type) {
            if(!currentData) return;
            let u = "";
            if(type === 'profile') u = currentData.author.avatar;
            if(type === 'cover') u = currentData.cover;
            if(type === 'dynamic') u = currentData.dynamic_cover;
            if(u) window.open(u, '_blank');
        }

        // --- HISTORY ---
        function addToHistory(data) {
            let h = JSON.parse(localStorage.getItem('tkHistory') || '[]');
            if(!h.find(x => x.id === data.id)) {
                h.unshift({
                    id: data.id,
                    title: data.meta.title,
                    cover: data.cover,
                    time: new Date().toLocaleTimeString()
                });
                if(h.length > 10) h.pop();
                localStorage.setItem('tkHistory', JSON.stringify(h));
                renderHistory();
            }
        }

        function renderHistory() {
            const h = JSON.parse(localStorage.getItem('tkHistory') || '[]');
            const list = document.getElementById('historyList');
            if(h.length === 0) list.innerHTML = '<p class="text-xs text-gray-500 text-center mt-10">No history yet.</p>';
            else {
                list.innerHTML = h.map(item => `
                    <div class="card p-2 flex gap-3 items-center">
                        <img src="/proxy_image?url=${encodeURIComponent(item.cover)}" class="w-10 h-10 rounded object-cover">
                        <div class="overflow-hidden flex-1">
                            <p class="text-xs font-bold truncate">${item.title || 'Video'}</p>
                            <p class="text-[10px] text-gray-500">${item.time}</p>
                        </div>
                    </div>
                `).join('');
            }
        }
        function clearHistory() {
            localStorage.removeItem('tkHistory');
            renderHistory();
        }
        renderHistory();

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
        fname = f"{name}.{type_}"
        return Response(stream_with_context(r.iter_content(chunk_size=4096)), content_type=ct, headers={"Content-Disposition": f"attachment; filename={fname}"})
    except: return "Error", 500

if __name__ == '__main__':
    app.run()

