from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import uuid
import re
import time

app = Flask(__name__)

# simple rate limiting
rate_limit = {}

def write_cookiefile():
    cookie_text = os.getenv("YOUTUBE_COOKIES", "")
    path = "/tmp/youtube_cookies.txt"
    if cookie_text:
        with open(path, "w") as f:
            f.write(cookie_text)
    return path if cookie_text else None

def validate_url(url: str):
    if not re.match(r"^(https?://)", url):
        return False
    return True

def apply_rate_limit(ip):
    now = time.time()
    if ip in rate_limit and now - rate_limit[ip] < 1.2:
        raise Exception("Too many requests")
    rate_limit[ip] = now

@app.route("/")
def home():
    return {"status": "OK", "backend": "sstube-clean"}

@app.route("/download")
def download():
    url = request.args.get("url")
    fmt = request.args.get("format", "mp4")
    quality = request.args.get("quality", "best")

    if not url or not validate_url(url):
        return jsonify({"error": "Invalid or missing URL"}), 400

    try:
        apply_rate_limit("client")
    except:
        return jsonify({"error": "Too many requests"}), 429

    cookiefile = write_cookiefile()

    temp_id = str(uuid.uuid4())
    output = f"/tmp/{temp_id}.%(ext)s"

    quality_map = {
        "360": "bestvideo[height<=360]+bestaudio/best",
        "480": "bestvideo[height<=480]+bestaudio/best",
        "720": "bestvideo[height<=720]+bestaudio/best",
        "1080": "bestvideo[height<=1080]+bestaudio/best",
        "best": "bestvideo+bestaudio/best"
    }

    ydl_opts = {
        "outtmpl": output,
        "cookiefile": cookiefile,
        "format": quality_map.get(quality, "bestvideo+bestaudio/best"),
        "merge_output_format": "mp4" if fmt == "mp4" else "mp3",
        "quiet": True,
        "noplaylist": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_path = ydl.prepare_filename(info)
            if fmt == "mp3":
                final_path = final_path.rsplit(".", 1)[0] + ".mp3"
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file(final_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
