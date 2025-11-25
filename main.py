from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import os
import uuid
import re
import time

app = FastAPI()

rate_limit = {}

def write_cookiefile():
    cookie_text = os.getenv("YOUTUBE_COOKIES", "")
    path = "/tmp/youtube_cookies.txt"
    if cookie_text:
        with open(path, "w") as f:
            f.write(cookie_text)
    return path if cookie_text else None

def validate_url(url: str):
    pattern = r"^(https?://)"
    if not re.match(pattern, url):
        raise HTTPException(400, "Invalid URL")

def apply_rate_limit(ip):
    now = time.time()
    if ip in rate_limit and now - rate_limit[ip] < 2:
        raise HTTPException(429, "Too many requests, slow down.")
    rate_limit[ip] = now

@app.get("/")
def root():
    return {"status": "OK", "service": "sstube-backend-pro"}

@app.get("/download")
def download(url: str = "", format: str = "mp4", quality: str = "best"):
    validate_url(url)
    apply_rate_limit("client")

    cookiefile = write_cookiefile()
    temp_id = str(uuid.uuid4())
    output = f"/tmp/{temp_id}.%(ext)s"

    format_map = {
        "360": "bestvideo[height<=360]+bestaudio/best",
        "480": "bestvideo[height<=480]+bestaudio/best",
        "720": "bestvideo[height<=720]+bestaudio/best",
        "1080": "bestvideo[height<=1080]+bestaudio/best",
        "best": "bestvideo+bestaudio/best"
    }

    ydl_opts = {
        "outtmpl": output,
        "cookiefile": cookiefile,
        "merge_output_format": "mp4" if format == "mp4" else "mp3",
        "format": format_map.get(quality, "bestvideo+bestaudio/best"),
        "noplaylist": True,
        "quiet": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_path = ydl.prepare_filename(info)

            if format == "mp3":
                final_path = final_path.rsplit(".", 1)[0] + ".mp3"

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    return FileResponse(final_path, filename=os.path.basename(final_path))
