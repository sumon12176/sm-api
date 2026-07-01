from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

def get_formats(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
        'cookiefile': None,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 Chrome/112.0.0.0 Mobile Safari/537.36',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

@app.route('/')
def home():
    return jsonify({"status": "SM Download Pro Backend", "version": "1.0"})

@app.route('/info', methods=['GET', 'POST'])
def video_info():
    url = request.args.get('url') or request.json.get('url', '') if request.is_json else request.form.get('url', '')
    if not url:
        return jsonify({"error": "url required"}), 400
    try:
        info = get_formats(url)
        video_formats = []
        audio_formats = []
        seen_heights = set()
        for f in (info.get('formats') or []):
            furl = f.get('url', '')
            if not furl:
                continue
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            height = f.get('height') or 0
            ext = f.get('ext', 'mp4')
            filesize = f.get('filesize') or f.get('filesize_approx') or 0
            abr = f.get('abr') or 0
            has_video = vcodec and vcodec != 'none'
            has_audio = acodec and acodec != 'none'
            if has_video and height >= 144 and height not in seen_heights:
                seen_heights.add(height)
                video_formats.append({
                    "quality": f"{height}p",
                    "ext": ext,
                    "mime": f"video/{ext}",
                    "url": furl,
                    "size": filesize,
                    "has_audio": has_audio
                })
            elif not has_video and has_audio and len(audio_formats) < 3:
                audio_formats.append({
                    "quality": f"MP3 {int(abr)}kbps" if abr else "Audio",
                    "ext": ext,
                    "mime": f"audio/{ext}",
                    "url": furl,
                    "size": filesize
                })
        video_formats.sort(key=lambda x: int(x['quality'].replace('p','')), reverse=True)
        return jsonify({
            "title": info.get('title', 'Unknown'),
            "thumbnail": info.get('thumbnail', ''),
            "duration": str(int(info.get('duration') or 0)),
            "channel": info.get('uploader') or info.get('channel', ''),
            "platform": info.get('extractor_key', ''),
            "video_formats": video_formats[:6],
            "audio_formats": audio_formats[:2]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
