from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile

app = Flask(__name__)
CORS(app)

TEMP_DIR = tempfile.gettempdir()

# HTML шаблон с твоим дизайном и AdSense
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2712778222245542" crossorigin="anonymous"></script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voxitly Ultra</title>
    <style>
        body { background: #050505; color: white; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; padding: 50px; }
        .box { background: rgba(20,20,20,0.9); border: 1px solid #ff0000; border-radius: 20px; padding: 40px; width: 100%; max-width: 450px; text-align: center; }
        h1 { color: #ff0000; letter-spacing: 10px; }
        input { width: 100%; padding: 15px; margin: 20px 0; border-radius: 10px; border: 1px solid #333; background: #111; color: white; box-sizing: border-box; }
        .btn { width: 100%; padding: 15px; background: #ff0000; color: white; border: none; border-radius: 10px; cursor: pointer; font-weight: bold; }
        #res.active { margin-top: 20px; display: block; }
        .thumb { width: 100%; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>VOXITLY</h1>
        <input type="text" id="url" placeholder="Paste YouTube link here...">
        <button class="btn" id="mainBtn" onclick="analyze()">ANALYZE</button>
        <div id="res" style="display:none;">
            <div id="info"></div>
            <button class="btn" style="background:#00ff41; color:black; margin-top:15px;" id="dlBtn" onclick="download()">DOWNLOAD</button>
        </div>
    </div>

    <script>
        let selectedId = "";
        async function analyze() {
            const url = document.getElementById('url').value;
            const btn = document.getElementById('mainBtn');
            btn.innerText = "ANALYZING...";
            try {
                const r = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
                const d = await r.json();
                if(d.error) throw new Error(d.error);
                selectedId = d.formats[0].id;
                document.getElementById('info').innerHTML = `<img src="${d.thumbnail}" class="thumb"><p>${d.title}</p>`;
                document.getElementById('res').style.display = "block";
                btn.innerText = "ANALYZE";
            } catch(e) { alert(e.message); btn.innerText = "ANALYZE"; }
        }
        function download() {
            const url = document.getElementById('url').value;
            window.location.href = `/api/download?url=${encodeURIComponent(url)}&f=${selectedId}`;
        }
    </script>
</body>
</html>
"""

def get_ydl_opts(f_id=None):
    opts = {
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }
    if os.path.exists('cookies.txt'):
        opts['cookiefile'] = 'cookies.txt'
    if f_id:
        opts['format'] = f_id
        opts['outtmpl'] = os.path.join(TEMP_DIR, '%(title)s.%(ext)s')
    return opts

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

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
    except Exception as e: return str(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
