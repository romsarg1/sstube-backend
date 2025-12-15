import os
import uuid
import subprocess
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp

app = FastAPI()

COOKIE_FILE = "/app/cookies.txt"


# -----------------------
# HEALTH CHECK
# -----------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------
# AUTO-DETECT METADATA
# -----------------------
@app.get("/meta")
def get_metadata(url: str = Query(...)):
    """
    Extracts metadata: title, thumbnail, author, duration, platform.
    """
    if not url or len(url) < 5:
        return JSONResponse({"status": "error", "message": "Invalid URL"}, status_code=400)

    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "extract_flat": False
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        metadata = {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "author": info.get("uploader") or info.get("channel") or info.get("creator"),
            "duration": info.get("duration"),
            "platform": info.get("extractor_key")
        }

        return JSONResponse({"status": "ok", "meta": metadata})

    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400
        )


# -----------------------
# MP4 DOWNLOAD
# -----------------------
@app.get("/download")
async def download(url: str = Query(...)):

    if not url or len(url) < 5:
        return JSONResponse({"error": "Invalid or missing URL"}, status_code=400)

    if not (
        "youtube.com" in url or "youtu.be" in url or 
        "tiktok.com" in url or "instagram.com" in url or
        "facebook.com" in url or "x.com" in url
    ):
        return JSONResponse({"error": "Unsupported URL"}, status_code=400)

    output_file = f"/app/{uuid.uuid4()}.mp4"

    cmd = [
        "yt-dlp",
        "-f", "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[acodec^=mp4a]/b",
        "--merge-output-format", "mp4",
        "--cookies", COOKIE_FILE,
        "-o", output_file,
        url
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0 or not os.path.exists(output_file):
        return JSONResponse({"error": "Video download failed"}, status_code=400)

    return FileResponse(output_file, media_type="video/mp4", filename="video.mp4")


# -----------------------
# MP3 DOWNLOAD
# -----------------------
@app.get("/mp3")
async def download_mp3(url: str = Query(...)):

    if not url or len(url) < 5:
        return JSONResponse({"error": "Invalid or missing URL"}, status_code=400)

    if not (
        "youtube.com" in url or "youtu.be" in url or 
        "tiktok.com" in url or "instagram.com" in url or
        "facebook.com" in url or "x.com" in url
    ):
        return JSONResponse({"error": "Unsupported URL"}, status_code=400)

    output_file = f"/app/{uuid.uuid4()}.mp3"

    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "192K",
        "--cookies", COOKIE_FILE,
        "-o", output_file,
        url
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0 or not os.path.exists(output_file):
        return JSONResponse({"error": "Audio download failed"}, status_code=400)

    return FileResponse(output_file, media_type="audio/mpeg", filename="audio.mp3")
