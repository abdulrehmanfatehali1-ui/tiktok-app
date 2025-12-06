from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import requests
import socket

app = Flask(__name__)

# --- Backend Logic ---

def get_file_size(url):
    """Fetches the file size (MB) without downloading the file."""
    try:
        response = requests.head(url, allow_redirects=True)
        size_in_bytes = int(response.headers.get('content-length', 0))
        if size_in_bytes == 0: return "Unknown"
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"
    except:
        return "Unknown"

def get_video_meta(url):
    api_url = "https://www.tikwm.com/api/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    params = {"url": url, "count": 12, "cursor": 0, "web": 1, "hd": 1}
    
    try:
        resp = requests.get(api_url, params=params, headers=headers)
        data = resp.json()
        
        if data.get("code") == 0:
            d = data["data"]
            
            # Prefer original cover, fallback to dynamic
            cover = d.get("origin_cover", d.get("cover"))
            
            # Fetch sizes (Optional enhancement - adds slight delay but useful)
            # vid_size = get_file_size(d.get("play")) 
            # For speed, we can skip fetching size here or do it in frontend logic
            
            return {
                "status": "success",
                "id": d.get("id"),
                "title": d.get("title", ""),
                "cover": cover, 
                "play_url": d.get("play"),
                "music_url": d.get("music"),
                "author_name": d.get("author", {}).get("nickname", "Unknown"),
                "author_avatar": d.get("author", {}).get("avatar"),
                "size": d.get("size", 0), # API sometimes provides size
                "stats": {
                    "views": d.get("play_count", 0),
                    "likes": d.get("digg_count", 0),
                    "comments": d.get("comment_count", 0),
                    "shares": d.get("share_count", 0)
                }
            }
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# --- Frontend Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Downloader Ultimate</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        body {
            font-family: 'Outfit', sans-serif;
            background-color: #0f172a;
            background-image: 
                radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
                radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
                radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
            color: white;
            min-height: 100vh;
        }

        .glass-panel {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .input-group {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s;
        }
        .input-group:focus-within {
            border-color: #ec4899;
            box-shadow: 0 0 20px rgba(236, 72, 153, 0.2);
        }

        .btn-gradient {
            background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
            transition: all 0.3s ease;
        }
        .btn-gradient:hover {
            opacity: 0.9;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px -5px rgba(236, 72, 153, 0.4);
        }

        /* Toast Notification */
        #toast {
            visibility: hidden;
            min-width: 250px;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 8px;
            padding: 16px;
            position: fixed;
            z-index: 50;
            left: 50%;
            bottom: 30px;
            transform: translateX(-50%);
            font-size: 14px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            opacity: 0;
            transition: opacity 0.3s, bottom 0.3s;
        }
        #toast.show {
            visibility: visible;
            opacity: 1;
            bottom: 50px;
        }

        .loader {
            border: 3px solid rgba(255,255,255,0.1);
            border-left-color: #ec4899;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .history-item:hover {
            background: rgba(255,255,255,0.05);
        }
    </style>
</head>
<body class="flex flex-col items-center justify-center p-4 min-h-screen">

    <div class="glass-panel w-full max-w-lg rounded-3xl p-6 relative overflow-hidden">
        
        <!-- Header -->
        <div class="flex justify-between items-center mb-6">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-pink-500 to-purple-600 flex items-center justify-center">
                    <i class="fa-brands fa-tiktok text-xl text-white"></i>
                </div>
                <div>
                    <h1 class="text-xl font-bold tracking-tight">TikTok Saver</h1>
                    <p class="text-[10px] text-slate-400 uppercase tracking-widest">Ultimate Edition</p>
                </div>
            </div>
            <button onclick="clearHistory()" class="text-xs text-slate-500 hover:text-red-400 transition" title="Clear History">
                <i class="fa-solid fa-trash"></i> History
            </button>
        </div>

        <!-- Input Area -->
        <div class="input-group rounded-2xl flex items-center p-2 mb-6">
            <input type="text" id="urlInput" placeholder="Paste link here..." 
                class="bg-transparent border-none outline-none text-sm text-white flex-1 px-3 py-2 placeholder-slate-500"
                onkeypress="handleEnter(event)">
            
            <div class="flex gap-2 pr-1">
                <button onclick="pasteLink()" class="w-8 h-8 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300 transition flex items-center justify-center" title="Paste">
                    <i class="fa-regular fa-clipboard"></i>
                </button>
                <button onclick="resetApp()" class="w-8 h-8 rounded-lg bg-slate-700/50 hover:bg-red-500/20 hover:text-red-400 text-slate-300 transition flex items-center justify-center" title="Clear">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
        </div>

        <button onclick="fetchInfo()" id="searchBtn" class="w-full btn-gradient py-3.5 rounded-xl font-semibold text-sm shadow-lg flex items-center justify-center gap-2">
            <span>Find Video</span>
            <i class="fa-solid fa-magnifying-glass"></i>
        </button>

        <!-- Loading -->
        <div id="loading" class="hidden flex justify-center items-center gap-3 my-8">
            <div class="loader"></div>
            <span class="text-sm text-slate-400 animate-pulse">Processing...</span>
        </div>

        <!-- Result Area -->
        <div id="resultArea" class="hidden mt-6 animate-fade-in">
            
            <div class="bg-slate-800/40 rounded-2xl p-4 border border-white/5 flex gap-4 relative overflow-hidden group">
                <!-- Glowing BG Effect -->
                <div class="absolute top-0 right-0 w-32 h-32 bg-pink-500/10 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>

                <!-- Thumbnail -->
                <div class="w-24 h-36 flex-shrink-0 bg-slate-900 rounded-lg overflow-hidden border border-white/10 shadow-lg">
                    <img id="thumb" src="" class="w-full h-full object-cover" alt="Cover">
                </div>

                <!-- Content -->
                <div class="flex-1 flex flex-col justify-between min-w-0 z-10">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <img id="avatar" src="" class="w-5 h-5 rounded-full border border-white/20">
                            <p id="author" class="text-xs font-semibold text-slate-300 truncate">Author</p>
                        </div>
                        <h3 id="videoTitle" class="text-sm font-medium leading-snug line-clamp-2 text-white/90 mb-2">Title</h3>
                        
                        <!-- Stats Badges -->
                        <div class="flex gap-2 text-[10px] text-slate-400">
                            <span class="bg-white/5 px-2 py-1 rounded flex items-center gap-1">
                                <i class="fa-solid fa-eye"></i> <span id="statPlay">0</span>
                            </span>
                            <span class="bg-white/5 px-2 py-1 rounded flex items-center gap-1">
                                <i class="fa-solid fa-heart text-pink-500"></i> <span id="statLike">0</span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Download Buttons with Size Badge Logic -->
            <div class="mt-4 grid gap-3">
                <a id="btnVideo" href="#" class="btn-gradient w-full py-3 rounded-xl text-center font-bold text-sm flex items-center justify-center gap-2 relative overflow-hidden group">
                    <div class="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition duration-300"></div>
                    <i class="fa-solid fa-video"></i> 
                    <span>Download Video</span>
                    <span id="vidSize" class="text-[10px] bg-black/20 px-2 py-0.5 rounded-md ml-1 opacity-75">HD</span>
                </a>
                
                <a id="btnAudio" href="#" class="bg-slate-700/50 hover:bg-slate-700 border border-white/5 w-full py-3 rounded-xl text-center font-medium text-sm flex items-center justify-center gap-2 text-slate-200 transition">
                    <i class="fa-solid fa-music text-pink-400"></i> 
                    <span>Download Audio</span>
                    <span class="text-[10px] bg-black/20 px-2 py-0.5 rounded-md ml-1 opacity-50">MP3</span>
                </a>
            </div>
        </div>

        <!-- History Section -->
        <div id="historySection" class="mt-8 border-t border-white/5 pt-4 hidden">
            <h4 class="text-xs font-semibold text-slate-500 mb-3 uppercase tracking-wider">Recent Downloads</h4>
            <div id="historyList" class="space-y-2 max-h-40 overflow-y-auto pr-1 scrollbar-thin">
                <!-- Items injected via JS -->
            </div>
        </div>

    </div>

    <!-- Toast UI -->
    <div id="toast">Message here</div>

    <script>
        // --- Utilities ---
        function showToast(msg, type='info') {
            const toast = document.getElementById("toast");
            toast.textContent = msg;
            toast.style.backgroundColor = type === 'error' ? '#ef4444' : '#333';
            toast.className = "show";
            setTimeout(() => { toast.className = toast.className.replace("show", ""); }, 3000);
        }

        function formatNum(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
            return num;
        }

        async function pasteLink() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('urlInput').value = text;
                showToast("Link Pasted!");
            } catch (err) {
                showToast("Allow clipboard permission", 'error');
            }
        }

        function resetApp() {
            document.getElementById('urlInput').value = '';
            document.getElementById('resultArea').classList.add('hidden');
            document.getElementById('urlInput').focus();
        }

        function handleEnter(e) {
            if (e.key === 'Enter') fetchInfo();
        }

        // --- Core Logic ---
        async function fetchInfo() {
            const url = document.getElementById('urlInput').value.trim();
            const loading = document.getElementById('loading');
            const resultArea = document.getElementById('resultArea');
            const btn = document.getElementById('searchBtn');

            if (!url) {
                showToast("Please paste a valid link", 'error');
                return;
            }

            loading.classList.remove('hidden');
            resultArea.classList.add('hidden');
            btn.disabled = true;
            btn.classList.add('opacity-50');

            try {
                const response = await fetch('/api/info', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (data.status === 'success') {
                    // Update UI
                    updateUI(data);
                    // Save to History
                    addToHistory(data);
                } else {
                    showToast("Video not found or private", 'error');
                }

            } catch (err) {
                showToast("Server connection failed", 'error');
            } finally {
                loading.classList.add('hidden');
                btn.disabled = false;
                btn.classList.remove('opacity-50');
            }
        }

        function updateUI(data) {
            // Using Proxy Routes for Images (Fast & Secure)
            const proxyCover = `/proxy_image?url=${encodeURIComponent(data.cover)}`;
            const proxyAvatar = `/proxy_image?url=${encodeURIComponent(data.author_avatar)}`;

            document.getElementById('thumb').src = proxyCover;
            document.getElementById('avatar').src = proxyAvatar;
            document.getElementById('author').textContent = data.author_name;
            document.getElementById('videoTitle').textContent = data.title || "No Caption";

            document.getElementById('statPlay').textContent = formatNum(data.stats.views);
            document.getElementById('statLike').textContent = formatNum(data.stats.likes);

            // Size Badge
            if (data.size) {
                 document.getElementById('vidSize').textContent = (data.size / (1024*1024)).toFixed(1) + " MB";
            } else {
                document.getElementById('vidSize').textContent = "HD";
            }

            // Download Links
            const vLink = `/proxy_download?url=${encodeURIComponent(data.play_url)}&name=${data.id}&type=mp4`;
            const aLink = `/proxy_download?url=${encodeURIComponent(data.music_url)}&name=${data.id}&type=mp3`;

            document.getElementById('btnVideo').href = vLink;
            document.getElementById('btnAudio').href = aLink;

            document.getElementById('resultArea').classList.remove('hidden');
        }

        // --- History System ---
        function addToHistory(data) {
            let history = JSON.parse(localStorage.getItem('tiktokHistory') || '[]');
            // Avoid duplicates
            if (!history.find(h => h.id === data.id)) {
                history.unshift({
                    id: data.id,
                    title: data.title || 'Video',
                    author: data.author_name,
                    cover: data.cover, // store raw url
                    time: new Date().toLocaleTimeString()
                });
                if (history.length > 5) history.pop(); // Keep only last 5
                localStorage.setItem('tiktokHistory', JSON.stringify(history));
                renderHistory();
            }
        }

        function renderHistory() {
            const history = JSON.parse(localStorage.getItem('tiktokHistory') || '[]');
            const list = document.getElementById('historyList');
            const section = document.getElementById('historySection');
            
            if (history.length === 0) {
                section.classList.add('hidden');
                return;
            }

            section.classList.remove('hidden');
            list.innerHTML = history.map(item => `
                <div class="history-item flex gap-3 p-2 rounded-lg cursor-pointer transition" onclick="quickLoad('${item.id}')"> <!-- Note: Real quick load would need more logic, here just placeholder -->
                   <div class="w-8 h-8 rounded bg-slate-700 overflow-hidden">
                        <img src="/proxy_image?url=${encodeURIComponent(item.cover)}" class="w-full h-full object-cover">
                   </div>
                   <div class="flex-1 min-w-0 flex flex-col justify-center">
                        <p class="text-xs text-white truncate">${item.title}</p>
                        <p class="text-[10px] text-slate-500">${item.author} • ${item.time}</p>
                   </div>
                </div>
            `).join('');
        }

        function clearHistory() {
            localStorage.removeItem('tiktokHistory');
            renderHistory();
            showToast("History Cleared");
        }

        // Load history on start
        renderHistory();

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
    if result:
        return jsonify(result)
    return jsonify({"status": "error"}), 400

@app.route('/proxy_image')
def proxy_image():
    """Fast Proxy for Images (Lightweight)"""
    img_url = request.args.get('url')
    if not img_url: return "No URL", 404
    
    if not img_url.startswith(('http://', 'https://')):
        img_url = "https://www.tikwm.com" + img_url

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        # Stream=True keeps memory usage low
        resp = requests.get(img_url, headers=headers, stream=True, timeout=5)
        return Response(resp.content, mimetype=resp.headers.get('content-type', 'image/jpeg'))
    except:
        return "", 404

@app.route('/proxy_download')
def proxy_download():
    """Download Proxy for Video/Audio"""
    file_url = request.args.get('url')
    file_id = request.args.get('name', 'tiktok')
    file_type = request.args.get('type', 'mp4')

    if not file_url: return "No URL", 400
    if not file_url.startswith(('http://', 'https://')): file_url = "https://www.tikwm.com" + file_url

    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.tikwm.com/"}
    try:
        req = requests.get(file_url, stream=True, headers=headers)
        content_type = "video/mp4" if file_type == 'mp4' else "audio/mpeg"
        filename = f"{file_id}.{file_type}"
        return Response(stream_with_context(req.iter_content(chunk_size=4096)),
                        content_type=content_type,
                        headers={"Content-Disposition": f"attachment; filename={filename}"})
    except Exception as e:
        return f"Error: {str(e)}"
if __name__ == '__main__':
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "127.0.0.1"

    print(f"\\n >>> Ultimate TikTok Downloader Running! <<<")
    print(f" >>> Open: http://{local_ip}:5000 \\n")
    
    # Vercel aur Local dono k liye ye sahi setting ha
    app.run(debug=True, host='0.0.0.0', port=5000)
