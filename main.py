import os, uuid, subprocess, threading, time
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp

app = FastAPI()

COOKIE_FILE = "/app/cookies.txt"
DOWNLOAD_DIR = "/tmp"


def delete_file_later(path, delay=180):
    def _delete():
        time.sleep(delay)
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
    threading.Thread(target=_delete, daemon=True).start()


@app.get("/info")
def info(url: str):
    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            data = ydl.extract_info(url, download=False)

        return {
            "title": data.get("title"),
            "thumbnail": data.get("thumbnail"),
            "uploader": data.get("uploader"),
            "duration": data.get("duration_string")
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/download")
def download(url: str, type: str = "mp4", quality: str = "best"):
    uid = str(uuid.uuid4())
    output = os.path.join(DOWNLOAD_DIR, f"{uid}.%(ext)s")

    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        title = "".join(c for c in info["title"] if c.isalnum() or c in " _-")[:80]

    if type == "mp3":
        cmd = [
            "yt-dlp", "-x",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
            "--cookies", COOKIE_FILE,
            "-o", output, url
        ]
        final = os.path.join(DOWNLOAD_DIR, f"{uid}.mp3")
        mime = "audio/mpeg"
        filename = f"{title}.mp3"
    else:
        q = quality if quality.isdigit() else "best"
        cmd = [
            "yt-dlp",
            "-f", f"bv*[height<={q}]+ba/b",
            "--merge-output-format", "mp4",
            "--cookies", COOKIE_FILE,
            "-o", output, url
        ]
        final = os.path.join(DOWNLOAD_DIR, f"{uid}.mp4")
        mime = "video/mp4"
        filename = f"{title}.mp4"

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if not os.path.exists(final):
        return JSONResponse({"error": "Download failed"}, status_code=500)

    delete_file_later(final)

    return FileResponse(final, media_type=mime, filename=filename)
