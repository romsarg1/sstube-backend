import os
import subprocess
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

COOKIE_FILE = "/app/cookies.txt"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/download")
async def download(url: str = Query(...)):
    if not url:
        return JSONResponse({"error": "missing url"}, status_code=400)

    output = "/app/video.mp4"

    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--cookies", COOKIE_FILE,
        "-o", output,
        url
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    return FileResponse(output, media_type="video/mp4", filename="video.mp4")
