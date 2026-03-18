from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import shutil

app = Flask(__name__)
CORS(app)

# Vercel's only writable folder
TEMP_DIR = "/tmp"
COOKIES_WORK_PATH = os.path.join(TEMP_DIR, "cookies.txt")

def prepare_cookies():
    """Moves cookies to /tmp to prevent Read-only error"""
    # Check both root and api folder for the source
    sources = ["cookies.txt", "api/cookies.txt"]
    for src in sources:
        if os.path.exists(src):
            shutil.copy(src, COOKIES_WORK_PATH)
            return True
    return False

def get_ydl_opts(f_id=None):
    prepare_cookies()
    opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # Emulating Android app to bypass "Sign in to confirm" errors
        'extractor_args': {'youtube': {'player_client': ['android'], 'skip': ['webpage']}},
        'user_agent': 'com.google.android.youtube/19.05.36 (Linux; U; Android 11; en_US; Pixel 4 XL Build/RP1A.200720.009)',
    }
    if os.path.exists(COOKIES_WORK_PATH):
        opts['cookiefile'] = COOKIES_WORK_PATH
    
    if f_id:
        opts['format'] = f_id
        opts['outtmpl'] = os.path.join(TEMP_DIR, '%(title)s.%(ext)s')
    return opts

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2712778222245542" crossorigin="anonymous"></script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voxitly Ultra | Downloader</title>
    <style>
        body { background: #050505; color: white; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .box { background: #111; border: 2px solid #ff0000; border-radius: 25px; padding: 40px; width: 90%; max-width: 400px; text-align: center; box-shadow: 0 0 25px #ff000033; }
        h1 { color: #ff0000; letter-spacing: 5px; margin-bottom: 25px; font-size: 2.5em; }
        input { width: 100%; padding: 15px; background: #000; border: 1px solid #333; color: white; border-radius: 12px; margin-bottom: 20px; box-sizing: border-box; outline: none; }
        input:focus { border-color: #ff0000; }
        .btn { width: 100%; padding: 15px; background: #ff0000; color: white; border: none; border-radius: 12px; cursor: pointer; font-weight: bold; text-transform: uppercase; }
        #res { display: none; margin-top: 25px; border-top: 1px solid #222; padding-top: 20px; }
        .thumb { width: 100%; border-radius: 15px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>VOXITLY</h1>
        <input type="text" id="url" placeholder="Paste YouTube link here...">
        <button class="btn" id="mainBtn" onclick="analyze()">Analyze Video</button>
        <div id="res">
            <div id="info"></div>
            <button class="btn" style="background:#00ff41; color:black; margin-top:15px;" onclick="download()">Download Now</button>
        </div>
    </div>
    <script>
        let selId = "";
        async function analyze() {
            const url = document.getElementById('url').value;
            const btn = document.getElementById('mainBtn');
            if(!url) return;
            btn.innerText = "ANALYZING...";
            try {
                const r = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
                const d = await r.json();
                if(d.error) throw new Error(d.error);
                selId = d.formats[0].id;
                document.getElementById('info').innerHTML = `<img src="${d.thumbnail}" class="thumb"><p>${d.title}</p>`;
                document.getElementById('res').style.display = "block";
                btn.innerText = "ANALYZE VIDEO";
            } catch(e) { alert("Error: " + e.message); btn.innerText = "ANALYZE VIDEO"; }
        }
        function download() {
            const url = document.getElementById('url').value;
            window.location.href = `/api/download?url=${encodeURIComponent(url)}&f=${selId}`;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/info')
def get_info():
    url = request.args.get('url')
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [{"id": f.get('format_id')} for f in info.get('formats', []) if f.get('url')]
            return jsonify({"title": info.get('title'), "thumbnail": info.get('thumbnail'), "formats": formats})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/download')
def download():
    url, f_id = request.args.get('url'), request.args.get('f')
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(f_id)) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
        return send_file(path, as_attachment=True)
    except Exception as e:
        return f"Error: {str(e)}"
