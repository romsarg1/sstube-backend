from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import uuid
import re
import time

app = Flask(__name__)

# === SIMPLE RATE LIMIT ===
rate_limit = {}

def apply_rate_limit(ip):
    now = time.time()
    if ip in rate_limit and now - rate_limit[ip] < 1:
        raise Exception("Too many requests, please slow down.")
    rate_limit[ip] = now

# === COOKIE FILE WRITER ===
def write_cookiefile():
    cookie_text = os.getenv("YOUTUBE_COOKIES", "")
    cookie_path = "/tmp/youtube_cookies.txt"
    if cookie_text:
        with open(cookie_path, "w") as f:
            f.write(cookie_text)
    return cookie_path if cookie_text else None

# === URL VALIDATION ===
def validate_url(url: str):
    pattern = r"^(https?://)"
    return re.match(pattern, url)

@app.route("/")
def home():
    return {"status": "OK", "service": "sstube-backend-railway"}

@app.route("/download")
def download():
    url = request.args.get("url")
    fmt = request.args.get("format", "mp4")
    quality = request.args.get("quality", "best")

    if not url or not validate_url(url):
        return jsonify({"error": "Invalid or missing URL"}), 400

    try:
        apply_rate_limit(request.remote_addr)
    except:
        return jsonify({"error": "Too many requests"}), 429

    cookiefile = write_cookiefile()
    temp_id = str(uuid.uuid4())
    outtmpl = f"/tmp/{temp_id}.%(ext)s"

    quality_map = {
        "360": "bestvideo[height<=360]+bestaudio/best",
        "480": "bestvideo[height<=480]+bestaudio/best",
        "720": "bestvideo[height<=720]+bestaudio/best",
        "1080": "bestvideo[height<=1080]+bestaudio/best",
        "best": "bestvideo+bestaudio/best"
    }

    ydl_opts = {
        "outtmpl": outtmpl,
        "cookiefile": cookiefile,
        "quiet": True,
        "noplaylist": True,
        "format": quality_map.get(quality, "bestvideo+bestaudio/best"),
        "merge_output_format": "mp4" if fmt == "mp4" else "mp3"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final = ydl.prepare_filename(info)
            if fmt == "mp3":
                final = final.rsplit(".", 1)[0] + ".mp3"
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file(final, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
