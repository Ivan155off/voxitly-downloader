from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile

app = Flask(__name__)
CORS(app)

TEMP_DIR = tempfile.gettempdir()

# Твой дизайн с интеграцией AdSense
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2712778222245542" crossorigin="anonymous"></script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voxitly Ultra | Downloader</title>
    <style>
        body { 
            background: #050505; color: white; font-family: 'Segoe UI', sans-serif; 
            display: flex; flex-direction: column; align-items: center; justify-content: center; 
            min-height: 100vh; margin: 0; padding: 20px;
        }
        .box { 
            background: rgba(15, 15, 15, 0.95); border: 2px solid #ff0000; 
            border-radius: 30px; padding: 40px; width: 100%; max-width: 450px; 
            text-align: center; box-shadow: 0 0 30px rgba(255,0,0,0.2);
        }
        h1 { color: #ff0000; letter-spacing: 10px; font-size: 2.5em; margin-bottom: 30px; }
        input { 
            width: 100%; padding: 15px; background: #111; border: 1px solid #333; 
            color: white; border-radius: 12px; margin-bottom: 20px; box-sizing: border-box;
        }
        .btn { 
            width: 100%; padding: 15px; background: #ff0000; color: white; 
            border: none; border-radius: 12px; font-weight: bold; cursor: pointer;
            transition: 0.3s; text-transform: uppercase;
        }
        .btn:hover { background: #cc0000; transform: scale(1.02); }
        #res { margin-top: 30px; display: none; text-align: left; }
        .thumb { width: 100%; border-radius: 15px; margin-bottom: 15px; }
        .info-text { font-size: 0.9em; margin-bottom: 15px; color: #ccc; }
    </style>
</head>
<body>
    <div class="box">
        <h1>VOXITLY</h1>
        <input type="text" id="url" placeholder="Вставь ссылку на видео...">
        <button class="btn" id="mainBtn" onclick="analyze()">Анализировать</button>
        
        <div id="res">
            <div id="info"></div>
            <button class="btn" style="background: #00ff41; color: black;" onclick="download()">Скачать лучшее качество</button>
        </div>
    </div>

    <script>
        let selectedFormat = "";

        async function analyze() {
            const url = document.getElementById('url').value;
            const btn = document.getElementById('mainBtn');
            if(!url) return;

            btn.innerText = "ПОДОЖДИТЕ...";
            try {
                const r = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
                const d = await r.json();
                if(d.error) throw new Error(d.error);

                selectedFormat = d.formats[0].id;
                document.getElementById('info').innerHTML = `
                    <img src="${d.thumbnail}" class="thumb">
                    <div class="info-text"><b>Название:</b> ${d.title}</div>
                `;
                document.getElementById('res').style.display = "block";
                btn.innerText = "АНАЛИЗИРОВАТЬ";
            } catch(e) {
                alert("Ошибка: " + e.message);
                btn.innerText = "АНАЛИЗИРОВАТЬ";
            }
        }

        function download() {
            const url = document.getElementById('url').value;
            window.location.href = `/api/download?url=${encodeURIComponent(url)}&f=${selectedFormat}`;
        }
    </script>
</body>
</html>
"""

def get_ydl_opts(f_id=None):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # Стратегия "Android": YouTube реже блокирует мобильных клиентов
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'user_agent': 'com.google.android.youtube/19.05.36 (Linux; U; Android 11; en_US; Pixel 4 XL Build/RP1A.200720.009)',
        'referer': 'https://www.youtube.com/',
    }
    # Подключаем куки, если файл существует на GitHub
    if os.path.exists('cookies.txt'):
        opts['cookiefile'] = 'cookies.txt'
    
    if f_id:
        opts['format'] = f_id
        opts['outtmpl'] = os.path.join(TEMP_DIR, '%(title)s.%(ext)s')
    return opts

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/info')
def get_info():
    url = request.args.get('url')
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
            # Берем только форматы с прямыми ссылками
            formats = [{"id": f.get('format_id'), "ext": f.get('ext')} for f in info.get('formats', []) if f.get('url')]
            
            if not formats:
                return jsonify({"error": "Не удалось найти доступные форматы."})

            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats
            })
    except Exception as e:
        # Если даже с куками блок — выводим понятную ошибку
        error_msg = str(e)
        if "confirm you're not a bot" in error_msg or "blocked" in error_msg:
            return jsonify({"error": "YouTube заблокировал сервер. Попробуй обновить cookies.txt или другое видео."})
        return jsonify({"error": error_msg})

@app.route('/api/download')
def download():
    url = request.args.get('url')
    f_id = request.args.get('f')
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(f_id)) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
        return send_file(path, as_attachment=True)
    except Exception as e:
        return f"Ошибка при скачивании: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
