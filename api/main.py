from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import shutil
import tempfile

app = Flask(__name__)
CORS(app)

# На Vercel запись разрешена только в /tmp
TEMP_DIR = "/tmp"
COOKIES_PATH = os.path.join(TEMP_DIR, "cookies.txt")

def setup_cookies():
    # Копируем куки из корня или папки api во временную папку /tmp
    # Это решает ошибку "Read-only file system"
    for p in ["cookies.txt", "api/cookies.txt"]:
        if os.path.exists(p):
            shutil.copy(p, COOKIES_PATH)
            break

def get_ydl_opts(f_id=None):
    setup_cookies()
    opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android'], 'skip': ['webpage']}},
        'user_agent': 'com.google.android.youtube/19.05.36 (Linux; U; Android 11; en_US; Pixel 4 XL Build/RP1A.200720.009)',
        'referer': 'https://www.youtube.com/',
    }
    if os.path.exists(COOKIES_PATH):
        opts['cookiefile'] = COOKIES_PATH
    if f_id:
        opts['format'] = f_id
        opts['outtmpl'] = os.path.join(TEMP_DIR, '%(title)s.%(ext)s')
    return opts

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2712778222245542" crossorigin="anonymous"></script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voxitly Ultra | Vercel Edition</title>
    <style>
        body { background: #050505; color: white; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }
        .box { background: #111; border: 2px solid #ff0000; border-radius: 25px; padding: 40px; width: 100%; max-width: 400px; text-align: center; box-shadow: 0 0 30px rgba(255,0,0,0.2); }
        h1 { color: #ff0000; letter-spacing: 10px; font-weight: 900; margin-bottom: 30px; }
        input { width: 100%; padding: 15px; background: #000; border: 1px solid #333; color: white; border-radius: 12px; margin-bottom: 20px; box-sizing: border-box; outline: none; }
        .btn { width: 100%; padding: 15px; background: #ff0000; color: white; border: none; border-radius: 12px; cursor: pointer; font-weight: bold; text-transform: uppercase; transition: 0.3s; }
        .btn:hover { background: #cc0000; }
        #res { display: none; margin-top: 25px; text-align: left; }
        .thumb { width: 100%; border-radius: 15px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>VOXITLY</h1>
        <input type="text" id="url" placeholder="Вставь ссылку...">
        <button class="btn" id="mainBtn" onclick="analyze()">Анализ</button>
        <div id="res">
            <div id="info"></div>
            <button class="btn" style="background:#00ff41; color:black; margin-top:15px;" onclick="download()">Скачать</button>
        </div>
    </div>
    <script>
        let fId = "";
        async function analyze() {
            const url = document.getElementById('url').value;
            const btn = document.getElementById('mainBtn');
            btn.innerText = "ЖДИ...";
            try {
                const r = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
                const d = await r.json();
                if(d.error) throw new Error(d.error);
                fId = d.formats[0].id;
                document.getElementById('info').innerHTML = `<img src="${d.thumbnail}" class="thumb"><p><b>${d.title}</b></p>`;
                document.getElementById('res').style.display = "block";
                btn.innerText = "АНАЛИЗ";
            } catch(e) { alert("Ошибка: " + e.message); btn.innerText = "АНАЛИЗ"; }
        }
        function download() {
            const url = document.getElementById('url').value;
            window.location.href = `/api/download?url=${encodeURIComponent(url)}&f=${fId}`;
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
            formats = [{"id": f.get('format_id'), "ext": f.get('ext')} for f in info.get('formats', []) if f.get('url')]
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
        return str(e)

# Важно для Vercel: переменная должна называться app
