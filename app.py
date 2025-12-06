from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import requests

app = Flask(__name__)

# --- Backend Logic ---
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
                    "likes": d.get("digg_count", 0),
                    "comments": d.get("comment_count", 0),
                    "shares": d.get("share_count", 0)
                }
            }
        return None
    except Exception as e:
        return None

# --- Frontend Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Saver Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <meta name="referrer" content="no-referrer"> 
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        body { font-family: 'Outfit', sans-serif; background-color: #0f172a; color: white; min-height: 100vh; }
        .glass-panel { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .btn-gradient { background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%); }
        .loader { border: 3px solid rgba(255,255,255,0.1); border-left-color: #ec4899; border-radius: 50%; width: 24px; height: 24px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="flex flex-col items-center justify-center p-4 min-h-screen">
    <div class="glass-panel w-full max-w-lg rounded-3xl p-6 relative overflow-hidden">
        <div class="text-center mb-6">
            <h1 class="text-xl font-bold tracking-tight">TikTok Saver</h1>
            <p class="text-xs text-slate-400">Ultimate Edition</p>
        </div>
        
        <div class="mb-6">
            <input type="text" id="urlInput" placeholder="Paste link here..." class="w-full bg-slate-800 p-3 rounded-lg text-white text-sm outline-none border border-slate-700 focus:border-pink-500">
        </div>

        <button onclick="fetchInfo()" id="searchBtn" class="w-full btn-gradient py-3 rounded-xl font-bold text-sm">Find Video</button>

        <div id="loading" class="hidden flex justify-center mt-4"><div class="loader"></div></div>
        
        <div id="resultArea" class="hidden mt-6 bg-slate-800/50 p-4 rounded-xl">
            <div class="flex gap-4">
                <img id="thumb" src="" class="w-20 h-28 object-cover rounded-lg bg-slate-900">
                <div class="flex-1">
                    <h3 id="videoTitle" class="text-sm font-bold line-clamp-2">Title</h3>
                    <p id="author" class="text-xs text-slate-400 mt-1">User</p>
                </div>
            </div>
            <div class="mt-4 gap-2 grid">
                <a id="btnVideo" href="#" class="btn-gradient w-full py-2 rounded-lg text-center text-sm font-bold">Download Video</a>
                <a id="btnAudio" href="#" class="bg-slate-700 w-full py-2 rounded-lg text-center text-sm">Download MP3</a>
            </div>
        </div>
        <div id="errorMsg" class="hidden mt-4 text-center text-red-400 text-sm"></div>
    </div>

    <script>
        async function fetchInfo() {
            const url = document.getElementById('urlInput').value.trim();
            if(!url) return;
            
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('resultArea').classList.add('hidden');
            document.getElementById('errorMsg').classList.add('hidden');

            try {
                const res = await fetch('/api/info', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url})
                });
                const data = await res.json();
                
                if(data.status === 'success') {
                    document.getElementById('thumb').src = data.cover;
                    document.getElementById('videoTitle').innerText = data.title;
                    document.getElementById('author').innerText = data.author_name;
                    
                    document.getElementById('btnVideo').href = `/proxy_download?url=${encodeURIComponent(data.play_url)}&name=${data.id}&type=mp4`;
                    document.getElementById('btnAudio').href = `/proxy_download?url=${encodeURIComponent(data.music_url)}&name=${data.id}&type=mp3`;
                    
                    document.getElementById('resultArea').classList.remove('hidden');
                } else {
                    document.getElementById('errorMsg').innerText = "Video not found!";
                    document.getElementById('errorMsg').classList.remove('hidden');
                }
            } catch(e) {
                document.getElementById('errorMsg').innerText = "Error fetching data";
                document.getElementById('errorMsg').classList.remove('hidden');
            } finally {
                document.getElementById('loading').classList.add('hidden');
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
    if result: return jsonify(result)
    return jsonify({"status": "error"}), 400

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

# Vercel k liye simple run command
if __name__ == '__main__':
    app.run()
