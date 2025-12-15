import os
import uuid
import subprocess
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp

app = FastAPI()

COOKIE_FILE = "/app/cookies.txt"
DOWNLOAD_DIR = "/tmp"


# -----------------------------
# HEALTH
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------------
# VIDEO INFO
# -----------------------------
@app.get("/info")
def info(url: str = Query(...)):
    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(url, download=False)

        return {
            "title": data.get("title"),
            "thumbnail": data.get("thumbnail"),
            "uploader": data.get("uploader"),
            "duration": data.get("duration_string"),
            "extractor": data.get("extractor")
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


# -----------------------------
# DOWNLOAD (CLOUDFLARE-SAFE)
# -----------------------------
@app.get("/download")
def download(
    url: str = Query(...),
    type: str = Query("mp4"),
    quality: str = Query("best")
):
    type = type.lower()

    uid = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{uid}.%(ext)s")

    if type == "mp3":
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
            "--cookies", COOKIE_FILE,
            "-o", output_template,
            url
        ]
        filename = "audio.mp3"
        mime = "audio/mpeg"
        final_file = os.path.join(DOWNLOAD_DIR, f"{uid}.mp3")

    else:
        q = quality if quality.isdigit() else "best"
        cmd = [
            "yt-dlp",
            "-f", f"bv*[height<={q}]+ba/b",
            "--merge-output-format", "mp4",
            "--cookies", COOKIE_FILE,
            "-o", output_template,
            url
        ]
        filename = "video.mp4"
        mime = "video/mp4"
        final_file = os.path.join(DOWNLOAD_DIR, f"{uid}.mp4")

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if not os.path.exists(final_file):
        return JSONResponse(
            {"error": "Download failed"},
            status_code=500
        )

    return FileResponse(
        final_file,
        media_type=mime,
        filename=filename
    )
