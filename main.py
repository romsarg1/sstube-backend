import subprocess
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, JSONResponse
import yt_dlp

app = FastAPI()

COOKIE_FILE = "/app/cookies.txt"


# -------------------------------------------------
# HEALTH CHECK (optional, safe)
# -------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------------------------------
# VIDEO METADATA (used by frontend preview)
# -------------------------------------------------
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
        return JSONResponse(
            {"error": str(e)},
            status_code=400
        )


# -------------------------------------------------
# DOWNLOAD (MP4 / MP3 / QUALITY) — STREAMING
# -------------------------------------------------
@app.get("/download")
def download(
    url: str = Query(...),
    type: str = Query("mp4"),
    quality: str = Query("best")
):
    """
    Parameters expected by existing frontend:
    - url: video URL
    - type: mp4 | mp3
    - quality: 360 | 480 | 720 | 1080 | best (mp4 only)
    """

    type = type.lower()

    if type not in ["mp4", "mp3"]:
        return JSONResponse(
            {"error": "Invalid type"},
            status_code=400
        )

    # ---------------------------
    # MP3 (audio only)
    # ---------------------------
    if type == "mp3":
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
            "--cookies", COOKIE_FILE,
            "-o", "-",          # stream to stdout
            url
        ]

        filename = "audio.mp3"
        mime = "audio/mpeg"

    # ---------------------------
    # MP4 (video + audio)
    # ---------------------------
    else:
        q = quality if quality.isdigit() else "best"

        cmd = [
            "yt-dlp",
            "-f", f"bv*[height<={q}]+ba/b",
            "--merge-output-format", "mp4",
            "--cookies", COOKIE_FILE,
            "-o", "-",          # stream to stdout
            url
        ]

        filename = "video.mp4"
        mime = "video/mp4"

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return StreamingResponse(
        process.stdout,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
