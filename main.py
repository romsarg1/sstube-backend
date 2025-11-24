
from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import uuid
import os
import time

app = FastAPI()
DOWNLOAD_DIR = "/tmp"

# Simple in-memory rate limit: max 10 downloads per IP per 60 seconds
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 10
RATE_LIMIT = {}


def check_rate_limit(ip: str):
    now = time.time()
    timestamps = RATE_LIMIT.get(ip, [])
    # keep only recent timestamps
    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(timestamps) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail="Too many requests, please slow down."
        )
    timestamps.append(now)
    RATE_LIMIT[ip] = timestamps


@app.get("/")
def root():
    return {"status": "ok", "service": "sstube-backend-pro"}


@app.get("/download")
def download_video(
    request: Request,
    url: str = Query(...),
    format: str = Query("mp4"),
    quality: str = Query("best")
):
    """
    Download video or audio from YouTube, TikTok, Instagram, Facebook, Twitter, etc.
    Params:
    - url: source video URL
    - format: 'mp4' or 'mp3'
    - quality: '360', '480', '720', '1080', or 'best'
    """

    client_ip = request.headers.get("x-forwarded-for", request.client.host)
    check_rate_limit(client_ip)

    video_id = str(uuid.uuid4())
    if format == "mp3":
        output_path = f"{DOWNLOAD_DIR}/{video_id}.mp3"
    else:
        output_path = f"{DOWNLOAD_DIR}/{video_id}.mp4"

    try:
        if format == "mp3":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{DOWNLOAD_DIR}/{video_id}.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        else:
            # Map quality to yt-dlp format selector
            base_video = "bestvideo[ext=mp4]"
            if quality.isdigit():
                h = int(quality)
                base_video = f"bestvideo[ext=mp4][height<={h}]"
            elif quality != "best":
                # Fallback if unknown
                base_video = "bestvideo[ext=mp4]"

            video_fmt = base_video
            audio_fmt = "bestaudio[ext=m4a]"
            ydl_format = f"{video_fmt}+{audio_fmt}/best[ext=mp4]"

            ydl_opts = {
                "format": ydl_format,
                "merge_output_format": "mp4",
                "outtmpl": f"{DOWNLOAD_DIR}/{video_id}.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(output_path):
            # Try to find actual output (yt-dlp may choose ext)
            for ext in (".mp4", ".m4a", ".webm", ".mp3"):
                candidate = f"{DOWNLOAD_DIR}/{video_id}{ext}"
                if os.path.exists(candidate):
                    output_path = candidate
                    break

        if not os.path.exists(output_path):
            return JSONResponse({"error": "Download failed"}, status_code=500)

        media_type = "audio/mpeg" if format == "mp3" else "video/mp4"
        file_name = "audio.mp3" if format == "mp3" else "video.mp4"

        return FileResponse(
            output_path,
            media_type=media_type,
            filename=file_name,
        )

    except HTTPException:
        # re-raise rate limit errors
        raise
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
