from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import uuid
import os

app = FastAPI()
DOWNLOAD_DIR = "/tmp"

@app.get("/")
def root():
    return {"status": "ok", "service": "sstube-backend"}

@app.get("/download")
def download_video(url: str = Query(...)):
    try:
        video_id = str(uuid.uuid4())
        output_path = f"{DOWNLOAD_DIR}/{video_id}.mp4"

        ydl_opts = {
            "format": "mp4",
            "outtmpl": output_path,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(output_path):
            return JSONResponse({"error": "Download failed"}, status_code=500)

        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename="video.mp4",
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
