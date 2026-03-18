from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import shutil
import tempfile

app = Flask(__name__)
CORS(app)

# Vercel allows writing ONLY to the /tmp folder
TEMP_DIR = "/tmp"
COOKIES_WORK_PATH = os.path.join(TEMP_DIR, "cookies.txt")

def prepare_cookies():
    """Moves cookies.txt to /tmp to avoid 'Read-only file system' error"""
    original_paths = ["cookies.txt", "api/cookies.txt"]
    for path in original_paths:
        if os.path.exists(path):
            shutil.copy(path, COOKIES_WORK_PATH)
            return True
    return False

def get_ydl_opts(f_id=None):
    prepare_cookies()
    
    opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # Android emulation for better stability
        'extractor_args': {'youtube': {'player_client': ['android'], 'skip': ['webpage']}},
        'user_agent': 'com.google.android.youtube/19.05.36 (Linux; U; Android 11; en_US; Pixel 4 XL Build/RP1A.200720.009)',
        'referer': 'https://www.youtube.com/',
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
    <title>Voxitly Ultra | Premium Video Downloader</title>
    <style>
        body { 
            background: #050505; color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            display: flex; flex-direction: column; align-items: center; justify-content: center; 
            min-height: 100vh; margin: 0; padding: 20px;
        }
        .container { 
            background: rgba(15, 15, 15, 0.95); border: 2px solid #ff0000; 
            border-radius: 30px; padding: 40px; width: 100%; max-width: 420px; 
            text-align: center; box-shadow: 0 0 50px rgba(255, 0, 0, 0.2);
        }
        h1 { 
            color: #ff0000; letter-spacing: 10px; font-size: 2.5em; 
            margin-bottom: 30px; font-weight: 900; text-transform: uppercase;
        }
        input { 
            width: 100%; padding: 18px; background: #000; border: 1px solid #333; 
            color: white; border-radius: 15px; margin-bottom: 25px; 
            box-sizing: border-box; outline: none; transition: 0.3s;
        }
        input:focus { border-color: #ff0000; box-shadow: 0 0 10px rgba(255, 0, 0, 0.5); }
        .btn { 
            width: 100%; padding: 18px; background: #ff0000; color: white; 
            border: none; border-radius: 15px; font-weight: bold; cursor: pointer;
            transition: 0.3s; text-transform: uppercase; letter-spacing: 2px;
        }
        .btn:hover { background: #cc0000; transform: translateY(-2px); }
        #result-area { margin-top: 30px; display: none; text-align: left; animation: fadeIn 0.6s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .thumbnail { width: 100%; border-radius: 20px; margin-bottom: 15px; border: 1px solid #222; }
        .video-title { font-size: 1.1em; font-weight: bold; color: #eee; margin-bottom: 15px; display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>VOXITLY</h1>
        <input type="text" id="videoUrl" placeholder="Enter YouTube URL here...">
        <button class="btn" id="actionBtn" onclick="analyzeVideo()">Analyze Video</button>
        
        <div id="result-area">
            <div id="videoDetails"></div>
            <button class="btn" style="background: #00ff41; color: black; margin-top: 20px;" onclick="startDownload()">Download Now</button>
            <p id="statusMsg" style="color: #888; font-size: 0.8em; margin-top: 15px; text-align: center;"></p>
        </div>
    </div>

    <script>
        let currentFormatId = "";

        async function analyzeVideo() {
            const url = document.getElementById('videoUrl').value;
            const btn = document.getElementById('actionBtn');
            const resArea = document.getElementById('result-area');
            if(!url) return;

            btn.innerText = "ANALYZING...";
            btn.disabled = true;

            try {
                const response = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
                const data = await response.json();
                
                if(data.error) throw new Error(data.error);

                currentFormatId = data.formats[0].id;
                document.getElementById('videoDetails').innerHTML = `
                    <img src="${data.thumbnail}" class="thumbnail">
                    <span class="video-title">${data.title}</span>
                `;
                resArea.style.display = "block";
                btn.innerText = "ANALYZE VIDEO";
                btn.disabled = false;
            } catch(e) {
                alert("Error: " + e.message);
                btn.innerText = "ANALYZE VIDEO";
                btn.disabled = false;
            }
        }

        function startDownload() {
            const url = document.getElementById('videoUrl').value;
            document.getElementById('statusMsg').innerText = "Processing download... please wait.";
            window.location.href = `/api/download?url=${encodeURIComponent(url)}&f=${currentFormatId}`;
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
            
            if not formats:
                return jsonify({"error": "No formats found. Please update cookies."})

            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats
            })
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
        return f"Download Error: {str(e)}"
