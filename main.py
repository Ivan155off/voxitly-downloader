from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile

app = Flask(__name__)
CORS(app)

TEMP_DIR = tempfile.gettempdir()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2712778222245542" crossorigin="anonymous"></script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voxitly Ultra | Professional Downloader</title>
    <style>
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes glow { from { text-shadow: 0 0 10px #ff0000; } to { text-shadow: 0 0 25px #ff0000; } }
        @keyframes bgMove { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        body { 
            background: linear-gradient(-45deg, #050505, #1a0000, #050505, #000);
            background-size: 400% 400%; animation: bgMove 15s ease infinite; color: white; font-family: 'Segoe UI', sans-serif; 
            display: flex; flex-direction: column; align-items: center; justify-content: flex-start; min-height: 100vh; margin: 0;
            padding: 60px 20px; box-sizing: border-box; overflow-x: hidden;
        }
        .ad-side { position: fixed; top: 50%; transform: translateY(-50%); width: 160px; height: 600px; background: rgba(255,255,255,0.02); border: 1px dashed rgba(255,0,0,0.15); display: flex; align-items: center; justify-content: center; color: #333; font-size: 11px; z-index: 10; text-transform: uppercase; letter-spacing: 2px; }
        .ad-left { left: 30px; } .ad-right { right: 30px; }
        .ad-bottom { width: 100%; max-width: 970px; height: 250px; margin-top: 100px; margin-bottom: 50px; background: rgba(255,255,255,0.02); border: 1px dashed rgba(255,0,0,0.15); display: flex; align-items: center; justify-content: center; color: #333; border-radius: 20px; text-transform: uppercase; letter-spacing: 2px; }
        @media (max-width: 1300px) { .ad-side { display: none; } }
        .container { display: flex; flex-direction: column; align-items: center; width: 100%; position: relative; }
        .box { background: rgba(10, 10, 10, 0.85); backdrop-filter: blur(25px); border: 1px solid rgba(255, 0, 0, 0.2); border-radius: 35px; padding: clamp(20px, 5vw, 50px); width: 100%; max-width: 500px; text-align: center; box-shadow: 0 0 80px rgba(0,0,0,1), 0 0 30px rgba(255,0,0,0.2); animation: fadeIn 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); position: relative; z-index: 5; }
        h1 { color: #ff0000; letter-spacing: 15px; margin: 0; font-size: clamp(1.8em, 8vw, 3em); animation: glow 2s infinite alternate; font-weight: 900; }
        .tagline { color: #555; font-size: 0.75em; margin-top: 12px; text-transform: uppercase; letter-spacing: 4px; }
        input { width: 100%; padding: 18px; background: rgba(15, 15, 15, 0.7); border: 1px solid #222; color: white; border-radius: 18px; margin: 30px 0 12px 0; box-sizing: border-box; outline: none; transition: 0.4s; font-size: 16px; }
        input:focus { border-color: #ff0000; box-shadow: 0 0 20px rgba(255,0,0,0.25); background: rgba(25, 25, 25, 0.8); }
        .btn { width: 100%; padding: 20px; background: #ff0000; color: white; border: none; border-radius: 18px; font-weight: 900; cursor: pointer; text-transform: uppercase; transition: 0.3s; letter-spacing: 2px; }
        .btn:hover { transform: translateY(-4px); box-shadow: 0 12px 25px rgba(255,0,0,0.4); background: #ff1a1a; }
        .dl-btn { background: #00ff41 !important; color: #000 !important; margin-top: 25px; box-shadow: 0 5px 15px rgba(0,255,65,0.2); }
        #res { max-height: 0; opacity: 0; transition: max-height 0.8s ease, opacity 0.5s ease; text-align: left; background: rgba(0,0,0,0.5); border-radius: 25px; overflow: hidden; }
        #res.active { max-height: 1500px; opacity: 1; margin-top: 35px; padding: 25px; border: 1px solid rgba(255,255,255,0.05); }
        .thumb { width: 100%; border-radius: 20px; margin-bottom: 15px; box-shadow: 0 8px 20px rgba(0,0,0,0.6); }
        label { font-size: 0.7em; color: #ff0000; margin: 15px 0 6px 5px; font-weight: bold; text-transform: uppercase; display: block; letter-spacing: 1px; }
        .vox-dropdown { position: relative; width: 100%; margin-bottom: 15px; }
        .vox-dropdown-header { background: rgba(35, 35, 35, 0.9); border: 1px solid #333; color: white; border-radius: 16px; padding: 18px; cursor: pointer; position: relative; transition: 0.3s; font-size: 0.95em; }
        .vox-dropdown-header::after { content: '▼'; position: absolute; right: 20px; color: #666; font-size: 0.8em; }
        .vox-dropdown-list { position: absolute; top: 105%; left: 0; width: 100%; background: #0f0f0f; border: 1px solid #ff0000; border-radius: 16px; max-height: 0; opacity: 0; visibility: hidden; overflow-y: auto; z-index: 9999; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
        .vox-dropdown.open .vox-dropdown-list { max-height: 250px; opacity: 1; visibility: visible; }
        .vox-dropdown-item { padding: 14px 20px; color: #bbb; cursor: pointer; border-bottom: 1px solid #1a1a1a; transition: 0.2s; }
        .vox-dropdown-item:hover { background: #220000; color: #ff0000; padding-left: 25px; }
        #status { color: #ffcc00; margin-top: 18px; font-size: 0.85em; text-align: center; font-weight: 500; }
    </style>
</head>
<body>
    <div class="ad-side ad-left">Ad Space</div>
    <div class="ad-side ad-right">Ad Space</div>
    <div class="container">
        <div class="box">
            <h1>VOXITLY</h1>
            <div class="tagline">Ultra Downloader</div>
            <input type="text" id="url" placeholder="Enter YouTube URL...">
            <button class="btn" id="mainBtn" onclick="analyze()">Analyze</button>
            <div id="res">
                <div id="info"></div>
                <div id="controls" style="display:none; opacity:0; transition: 0.5s;">
                    <label>Format</label>
                    <div class="vox-dropdown" id="typeDropdown">
                        <div class="vox-dropdown-header" id="typeHeader">Video</div>
                        <div class="vox-dropdown-list">
                            <div class="vox-dropdown-item" data-value="video">Video</div>
                            <div class="vox-dropdown-item" data-value="audio">Audio (MP3/WebM)</div>
                        </div>
                    </div>
                    <label>Quality</label>
                    <div class="vox-dropdown" id="qualityDropdown">
                        <div class="vox-dropdown-header" id="qualityHeader">Loading...</div>
                        <div class="vox-dropdown-list" id="qualityList"></div>
                    </div>
                    <button class="btn dl-btn" id="dlBtn" onclick="download()">Download Now</button>
                    <div id="status"></div>
                </div>
            </div>
        </div>
        <div class="ad-bottom">Premium Ad Placement Slot</div>
    </div>
    <script>
        let videoData = [];
        let selectedType = "video";
        let selectedFormatId = "";

        function initCustomDropdowns() {
            document.querySelectorAll('.vox-dropdown').forEach(dropdown => {
                const header = dropdown.querySelector('.vox-dropdown-header');
                header.onclick = (e) => {
                    e.stopPropagation();
                    document.querySelectorAll('.vox-dropdown.open').forEach(d => { if(d !== dropdown) d.classList.remove('open'); });
                    dropdown.classList.toggle('open');
                };
            });
            document.onclick = () => document.querySelectorAll('.vox-dropdown.open').forEach(d => d.classList.remove('open'));
        }

        function handleItemClick(dropdownId, item) {
            const dropdown = document.getElementById(dropdownId);
            const header = dropdown.querySelector('.vox-dropdown-header');
            header.innerText = item.innerText;
            dropdown.classList.remove('open');
            if(dropdownId === 'typeDropdown') { selectedType = item.dataset.value; updateQualityList(); }
            else { selectedFormatId = item.dataset.value; document.getElementById('dlBtn').innerText = `Download (${item.innerText})`; }
        }

        async function analyze() {
            const urlInput = document.getElementById('url');
            if(!urlInput.value) return;
            const btn = document.getElementById('mainBtn');
            const res = document.getElementById('res');
            btn.innerText = "Analyzing...";
            try {
                const r = await fetch(`/api/info?url=${encodeURIComponent(urlInput.value)}`);
                const d = await r.json();
                if(d.error) throw new Error(d.error);
                videoData = d.formats;
                document.getElementById('info').innerHTML = `<img src="${d.thumbnail}" class="thumb"><div style="font-weight: bold; margin-bottom: 10px;">${d.title}</div>`;
                document.getElementById('controls').style.display = "block";
                setTimeout(() => { res.classList.add('active'); document.getElementById('controls').style.opacity = "1"; updateQualityList(); btn.innerText = "Analyze"; }, 100);
            } catch(e) { alert("Error: " + e.message); btn.innerText = "Analyze"; }
        }

        function updateQualityList() {
            const list = document.getElementById('qualityList');
            const header = document.getElementById('qualityHeader');
            list.innerHTML = "";
            const filtered = videoData.filter(f => selectedType === 'video' ? f.v : !f.v);
            filtered.forEach((f, index) => {
                const item = document.createElement('div');
                item.className = 'vox-dropdown-item';
                item.dataset.value = f.id;
                const label = selectedType === 'video' ? `${f.res} (${f.ext})` : `${f.abr} kbps`;
                item.innerText = label;
                if(index === 0) { selectedFormatId = f.id; header.innerText = label; document.getElementById('dlBtn').innerText = `Download (${label})`; }
                item.onclick = (e) => { e.stopPropagation(); handleItemClick('qualityDropdown', item); };
                list.appendChild(item);
            });
        }

        document.addEventListener('DOMContentLoaded', initCustomDropdowns);
        document.querySelectorAll('#typeDropdown .vox-dropdown-item').forEach(item => { item.onclick = (e) => { e.stopPropagation(); handleItemClick('typeDropdown', item); }; });

        function download() {
            const url = document.getElementById('url').value;
            const status = document.getElementById('status');
            status.innerText = "🚀 Processing... Please wait.";
            window.location.href = `/api/download?url=${encodeURIComponent(url)}&f=${selectedFormatId}`;
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
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        # Ограничиваем время ожидания, чтобы сайт не висел вечно
        'socket_timeout': 10,
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
            # Используем extract_flat=False, но ограничиваем поиск
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({"error": "Failed to get video info."})
            
            formats = []
            for f in info.get('formats', []):
                # Собираем только те, у которых есть ссылка
                if f.get('url'):
                    vcodec = f.get('vcodec', 'none')
                    is_video = vcodec != 'none' and vcodec is not None
                    
                    formats.append({
                        "id": f.get('format_id'),
                        "ext": f.get('ext', 'mp4'),
                        "res": f.get('resolution') or f.get('format_note') or ("Video" if is_video else "Audio"),
                        "abr": f.get('abr') or 0,
                        "v": is_video
                    })
            
            if not formats:
                return jsonify({"error": "No available formats for this video."})

            return jsonify({
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail', ''),
                "formats": formats
            })
    except Exception as e:
        return jsonify({"error": f"YouTube blocked request. Please update cookies.txt."})

@app.route('/api/download')
def download():
    url, f_id = request.args.get('url'), request.args.get('f')
    try:
        with yt_dlp.YoutubeDL(get_ydl_opts(f_id)) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
        return send_file(path, as_attachment=True)
    except Exception as e:
        return f"Download failed. YouTube might have restricted this file."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
