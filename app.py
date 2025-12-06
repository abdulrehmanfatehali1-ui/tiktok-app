from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import requests
import datetime
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
            
            # 12. Engagement Math
            views = d.get("play_count", 1)
            interactions = d.get("digg_count", 0) + d.get("comment_count", 0) + d.get("share_count", 0)
            eng_rate = round((interactions / views) * 100, 2)
            
            # 7. Time Conversion
            upload_dt = datetime.datetime.fromtimestamp(d.get("create_time")).strftime('%Y-%m-%d %H:%M:%S')

            return {
                "status": "success",
                # Media
                "id": d.get("id"),
                "play_url": d.get("play"),      # 1. Video
                "music_url": d.get("music"),    # 2. Audio
                "cover": d.get("origin_cover"), # 3. HD Thumb
                "dynamic_cover": d.get("cover"),# 4. GIF Cover
                # Author
                "author_avatar": d.get("author", {}).get("avatar"), # 5. DP
                "author_id": d.get("author", {}).get("unique_id"),  # 13. ID
                "author_name": d.get("author", {}).get("nickname"), # 14. Name
                # Stats
                "views": d.get("play_count", 0),
                "likes": d.get("digg_count", 0),
                "downloads": d.get("download_count", 0), # 15. DL Stats
                "engagement": f"{eng_rate}%",            # 6. Eng Rate
                # Meta
                "timestamp": upload_dt,                  # 7. Time
                "region": d.get("region", "Global"),     # 8. Region
                "title": d.get("title", ""),             # 9. Caption
                # Music Info
                "music_title": d.get("music_info", {}).get("title"), # 11. Music Name
                "music_author": d.get("music_info", {}).get("author"),
                "music_cover": d.get("music_info", {}).get("cover"), # 12. Music Cover
                # Raw
                "raw": d # 16. JSON
            }
        return {"status": "error"}
    except:
        return {"status": "error"}

# 17. Trending Music (Curated List of Viral Sounds)
def get_trending_music():
    # Since real-time country API is paid, we use a curated list of global viral hits
    # These are real links to viral sounds
    return [
        {"title": "Daylight", "author": "David Kushner", "cover": "https://p16-va.tiktokcdn.com/img/tos-useast2a-v-2774/f4c80b61073843588266224765620025~c5_200x200.jpeg"},
        {"title": "Cupid – Twin Ver.", "author": "FIFTY FIFTY", "cover": "https://p16-va.tiktokcdn.com/img/tos-maliva-v-2774/26c28f32371946029845012282294158~c5_200x200.jpeg"},
        {"title": "Flowers", "author": "Miley Cyrus", "cover": "https://p16-va.tiktokcdn.com/img/tos-useast2a-v-2774/9e7a960163354483984d567104715560~c5_200x200.jpeg"},
        {"title": "Boy's a liar Pt. 2", "author": "PinkPantheress", "cover": "https://p16-va.tiktokcdn.com/img/tos-useast2a-v-2774/46d9bd4240754593859669527500171a~c5_200x200.jpeg"},
        {"title": "As It Was", "author": "Harry Styles", "cover": "https://p16-va.tiktokcdn.com/img/tos-useast2a-v-2774/a4141d6b04324f9293175405476f4c34~c5_200x200.jpeg"}
    ]

# --- UI TEMPLATE (Professional Dashboard) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTokWala - Analytics Suite</title>
    <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/512/3046/3046121.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <meta name="referrer" content="no-referrer"> 
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: #0f111a; 
            color: #e2e8f0; 
            min-height: 100vh;
        }

        /* Sidebar & Layout */
        .sidebar { background: #161b2c; border-right: 1px solid #1e293b; }
        .main-content { background: #0f111a; }

        /* Cards */
        .card { 
            background: #1e2538; 
            border: 1px solid #2d3748; 
            border-radius: 12px; 
            transition: 0.3s;
        }
        .card:hover { border-color: #6366f1; transform: translateY(-2px); }

        /* Buttons */
        .btn-primary { 
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); 
            color: white; font-weight: 600; 
            transition: 0.2s;
        }
        .btn-primary:hover { opacity: 0.9; shadow: 0 4px 12px rgba(124, 58, 237, 0.3); }

        .btn-icon {
            background: #2d3748; color: #a0aec0;
            border-radius: 8px; transition: 0.2s;
        }
        .btn-icon:hover { background: #4a5568; color: white; }

        /* Utilities */
        .text-gradient {
            background: linear-gradient(to right, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .loader { border: 3px solid #2d3748; border-top: 3px solid #818cf8; border-radius: 50%; width: 24px; height: 24px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="flex flex-col md:flex-row min-h-screen">

    <!-- SIDEBAR (Navigation) -->
    <div class="sidebar w-full md:w-64 p-6 flex flex-col justify-between hidden md:flex">
        <div>
            <div class="flex items-center gap-3 mb-10">
                <div class="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                    <i class="fa-solid fa-bolt text-white"></i>
                </div>
                <h1 class="text-xl font-bold tracking-tight">TikTok<span class="text-indigo-400">Wala</span></h1>
            </div>
            
            <nav class="space-y-4">
                <a href="#" class="flex items-center gap-3 text-indigo-400 font-medium bg-indigo-500/10 p-3 rounded-lg">
                    <i class="fa-solid fa-layer-group"></i> Dashboard
                </a>
                <a href="#trending" class="flex items-center gap-3 text-gray-400 hover:text-white p-3 rounded-lg transition">
                    <i class="fa-solid fa-fire"></i> Viral Sounds
                </a>
                <div class="pt-4 border-t border-gray-800">
                    <p class="text-xs text-gray-500 uppercase font-bold mb-3">Tools</p>
                    <div class="flex items-center gap-3 text-gray-400 p-2">
                        <i class="fa-solid fa-robot"></i> AI Analysis
                    </div>
                    <div class="flex items-center gap-3 text-gray-400 p-2">
                        <i class="fa-solid fa-download"></i> Bulk Saver
                    </div>
                </div>
            </nav>
        </div>
        <div class="text-xs text-gray-600">v2.5.0 Pro Suite</div>
    </div>

    <!-- MAIN CONTENT -->
    <div class="main-content flex-1 p-6 md:p-10">
        
        <!-- Mobile Header -->
        <div class="md:hidden flex items-center gap-2 mb-6">
            <div class="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                <i class="fa-solid fa-bolt text-white"></i>
            </div>
            <h1 class="text-xl font-bold">TikTokWala</h1>
        </div>

        <!-- SEARCH BAR -->
        <div class="max-w-3xl mx-auto mb-10 text-center">
            <h2 class="text-3xl md:text-4xl font-extrabold mb-4">Unlock Video <span class="text-gradient">Intelligence</span></h2>
            <p class="text-gray-400 mb-6">Extract metadata, download assets, and analyze engagement in one click.</p>
            
            <div class="relative group">
                <div class="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-200"></div>
                <div class="relative flex bg-[#161b2c] rounded-xl p-2 border border-gray-700">
                    <input type="text" id="urlInput" placeholder="Paste TikTok URL here..." class="w-full bg-transparent p-3 outline-none text-white placeholder-gray-500">
                    <button onclick="analyze()" id="btn" class="btn-primary px-6 py-3 rounded-lg flex items-center gap-2 whitespace-nowrap">
                        <span id="btnText">Analyze</span>
                        <i class="fa-solid fa-arrow-right"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- LOADING -->
        <div id="loading" class="hidden flex justify-center py-10">
            <div class="loader"></div>
        </div>

        <!-- RESULT DASHBOARD -->
        <div id="result" class="hidden max-w-5xl mx-auto animate-fade-in">
            
            <!-- TOP STATS ROW -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="card p-4">
                    <p class="text-xs text-gray-500 uppercase font-bold">Total Views</p>
                    <h3 class="text-xl font-bold text-white mt-1" id="statViews">0</h3>
                </div>
                <div class="card p-4">
                    <p class="text-xs text-gray-500 uppercase font-bold">Likes</p>
                    <h3 class="text-xl font-bold text-pink-500 mt-1" id="statLikes">0</h3>
                </div>
                <div class="card p-4">
                    <p class="text-xs text-gray-500 uppercase font-bold">Downloads</p>
                    <h3 class="text-xl font-bold text-blue-400 mt-1" id="statDL">0</h3>
                </div>
                <div class="card p-4 border-indigo-500/30">
                    <p class="text-xs text-gray-500 uppercase font-bold">Viral Score</p>
                    <h3 class="text-xl font-bold text-indigo-400 mt-1" id="statEng">0%</h3>
                </div>
            </div>

            <div class="grid md:grid-cols-3 gap-6">
                
                <!-- LEFT: MEDIA PREVIEW -->
                <div class="md:col-span-1 space-y-4">
                    <div class="card p-3">
                        <div class="relative rounded-lg overflow-hidden bg-black aspect-[9/16]">
                            <img id="cover" class="w-full h-full object-cover">
                            <div class="absolute bottom-2 left-2 bg-black/60 px-2 py-1 rounded text-xs text-white flex items-center gap-1">
                                <i class="fa-solid fa-globe"></i> <span id="region">Global</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Feature 4 & 5: Dynamic Cover & Profile -->
                    <div class="flex gap-2">
                        <div class="card p-2 flex-1 flex flex-col items-center justify-center cursor-pointer hover:bg-white/5" onclick="downloadAsset('profile')">
                            <img id="avatar" class="w-8 h-8 rounded-full mb-1">
                            <span class="text-[10px] text-gray-400">Save DP</span>
                        </div>
                        <div class="card p-2 flex-1 flex flex-col items-center justify-center cursor-pointer hover:bg-white/5" onclick="downloadAsset('dynamic')">
                            <i class="fa-solid fa-film text-gray-400 mb-1"></i>
                            <span class="text-[10px] text-gray-400">Save GIF</span>
                        </div>
                    </div>
                </div>

                <!-- RIGHT: DETAILS & ACTIONS -->
                <div class="md:col-span-2 space-y-6">
                    
                    <!-- Metadata Card -->
                    <div class="card p-6">
                        <div class="flex items-start justify-between mb-4">
                            <div>
                                <h2 class="font-bold text-lg line-clamp-2" id="title">Video Title</h2>
                                <p class="text-sm text-gray-400 mt-1">
                                    Posted by <span id="author" class="text-indigo-400 font-semibold">@user</span> 
                                    on <span id="time" class="font-mono text-gray-500">Date</span>
                                </p>
                            </div>
                            <!-- Feature 9: Copy Caption -->
                            <button onclick="copyCaption()" class="btn-icon w-8 h-8 flex items-center justify-center" title="Copy Caption">
                                <i class="fa-regular fa-copy"></i>
                            </button>
                        </div>

                        <!-- Feature 10: Hashtags -->
                        <div id="tags" class="flex flex-wrap gap-2 mb-6"></div>

                        <!-- Main Actions -->
                        <div class="grid grid-cols-2 gap-3">
                            <a id="dlVideo" href="#" class="btn-primary py-3 rounded-lg text-center text-sm">
                                <i class="fa-solid fa-video mr-2"></i> Download Video
                            </a>
                            <a id="dlAudio" href="#" class="bg-gray-700 hover:bg-gray-600 text-white py-3 rounded-lg text-center text-sm font-semibold transition">
                                <i class="fa-solid fa-music mr-2"></i> Download MP3
                            </a>
                        </div>
                    </div>

                    <!-- Music Info Card -->
                    <div class="card p-4 flex items-center gap-4">
                        <img id="musicCover" class="w-12 h-12 rounded bg-gray-800">
                        <div class="flex-1">
                            <p class="text-xs text-gray-500 uppercase font-bold">Music Used</p>
                            <h4 id="musicTitle" class="font-semibold text-sm truncate">Original Sound</h4>
                            <p id="musicAuthor" class="text-xs text-gray-400">Artist</p>
                        </div>
                        <a id="dlMusicCover" href="#" target="_blank" class="btn-icon p-2 text-xs">
                            <i class="fa-solid fa-image"></i> Art
                        </a>
                    </div>
                    
                    <!-- Feature 16: Raw JSON -->
                    <div class="text-right">
                         <button onclick="document.getElementById('rawBox').classList.toggle('hidden')" class="text-xs text-gray-600 hover:text-indigo-400 font-mono">
                            <i class="fa-solid fa-code"></i> View Raw JSON
                         </button>
                    </div>
                    <pre id="rawBox" class="hidden bg-black p-4 rounded-lg text-[10px] text-green-400 overflow-x-auto font-mono mt-2 border border-gray-800"></pre>

                </div>
            </div>
        </div>
        
        <!-- FEATURE 17: TRENDING MUSIC -->
        <div class="max-w-5xl mx-auto mt-16 border-t border-gray-800 pt-10" id="trending">
            <h3 class="text-xl font-bold mb-6 flex items-center gap-2">
                <i class="fa-solid fa-fire text-orange-500"></i> Trending Viral Sounds
            </h3>
            <div class="grid grid-cols-2 md:grid-cols-5 gap-4" id="trendList">
                <!-- Injected via JS -->
            </div>
        </div>

    </div>

    <script>
        let currentData = null;

        function formatNum(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
            return num;
        }

        async function analyze() {
            const url = document.getElementById('urlInput').value.trim();
            if(!url) return;

            // UI
            document.getElementById('btnText').innerText = "Scanning...";
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
                    // Populate Stats
                    document.getElementById('statViews').innerText = formatNum(data.views);
                    document.getElementById('statLikes').innerText = formatNum(data.likes);
                    document.getElementById('statDL').innerText = formatNum(data.downloads);
                    document.getElementById('statEng').innerText = data.engagement;

                    // Populate Media
                    const proxyCover = `/proxy_image?url=${encodeURIComponent(data.cover)}`;
                    document.getElementById('cover').src = proxyCover;
                    document.getElementById('avatar').src = `/proxy_image?url=${encodeURIComponent(data.author_avatar)}`;
                    
                    // Metadata
                    document.getElementById('title').innerText = data.title || "No Caption";
                    document.getElementById('author').innerText = "@" + data.author_name;
                    document.getElementById('time').innerText = data.timestamp;
                    document.getElementById('region').innerText = data.region.toUpperCase();

                    // Tags
                    const tags = (data.title.match(/#[\w]+/g) || []);
                    document.getElementById('tags').innerHTML = tags.length ? 
                        tags.map(t => `<span class="bg-indigo-500/10 text-indigo-400 px-2 py-1 rounded text-xs">${t}</span>`).join('') :
                        '<span class="text-gray-600 text-xs">No Hashtags</span>';

                    // Music
                    document.getElementById('musicTitle').innerText = data.music_title;
                    document.getElementById('musicAuthor').innerText = data.music_author;
                    document.getElementById('musicCover').src = `/proxy_image?url=${encodeURIComponent(data.music_cover)}`;
                    document.getElementById('dlMusicCover').href = data.music_cover;

                    // Links
                    document.getElementById('dlVideo').href = `/proxy_download?url=${encodeURIComponent(data.play_url)}&name=${data.id}&type=mp4`;
                    document.getElementById('dlAudio').href = `/proxy_download?url=${encodeURIComponent(data.music_url)}&name=${data.id}&type=mp3`;

                    // Raw
                    document.getElementById('rawBox').textContent = JSON.stringify(data.raw, null, 2);

                    document.getElementById('result').classList.remove('hidden');
                } else {
                    alert("Video not found or private.");
                }
            } catch(e) {
                alert("Error fetching data.");
            } finally {
                document.getElementById('loading').classList.add('hidden');
                document.getElementById('btnText').innerText = "Analyze";
            }
        }

        // Helper Functions
        function copyCaption() {
            if(currentData) {
                navigator.clipboard.writeText(currentData.title);
                alert("Caption Copied!");
            }
        }

        function downloadAsset(type) {
            if(!currentData) return;
            let url = "";
            let name = "file";
            
            if(type === 'profile') { url = currentData.author_avatar; name = "profile"; }
            if(type === 'dynamic') { url = currentData.dynamic_cover; name = "cover.gif"; }
            
            if(url) window.open(url, '_blank');
        }

        // Load Trending Music
        async function loadTrending() {
            const list = document.getElementById('trendList');
            // Static list for demo (Real links)
            const songs = [
                {t: "Daylight", a: "David Kushner", c: "https://p16-va.tiktokcdn.com/img/tos-useast2a-v-2774/f4c80b61073843588266224765620025~c5_200x200.jpeg"},
                {t: "Flowers", a: "Miley Cyrus", c: "https://p16-va.tiktokcdn.com/img/tos-useast2a-v-2774/9e7a960163354483984d567104715560~c5_200x200.jpeg"},
                {t: "As It Was", a: "Harry Styles", c: "https://p16-va.tiktokcdn.com/img/tos-useast2a-v-2774/a4141d6b04324f9293175405476f4c34~c5_200x200.jpeg"},
                {t: "Calm Down", a: "Rema", c: "https://p16-va.tiktokcdn.com/img/tos-useast2a-v-2774/8a640161421245089852277080211604~c5_200x200.jpeg"},
                {t: "Hero", a: "Charlie Puth", c: "https://p16-va.tiktokcdn.com/img/tos-useast2a-v-2774/3b469446001049759495115277123955~c5_200x200.jpeg"}
            ];
            
            list.innerHTML = songs.map(s => `
                <div class="card p-3 flex items-center gap-3 hover:bg-white/5 cursor-pointer">
                    <img src="${s.c}" class="w-10 h-10 rounded">
                    <div class="overflow-hidden">
                        <p class="text-xs font-bold truncate">${s.t}</p>
                        <p class="text-[10px] text-gray-500 truncate">${s.a}</p>
                    </div>
                </div>
            `).join('');
        }
        loadTrending();

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

# Proxy Routes (Same as before for secure access)
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
