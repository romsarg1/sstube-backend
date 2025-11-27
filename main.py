import os
import uuid
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
    # Basic URL validation
    if not url or len(url) < 5:
        return JSONResponse(
            {"error": "Invalid or missing URL"},
            status_code=400
        )

    # Only allow platforms yt-dlp supports
    if not (
        "youtube.com" in url 
        or "youtu.be" in url 
        or "tiktok.com" in url
        or "instagram.com" in url
        or "facebook.com" in url
        or "x.com" in url
    ):
        return JSONResponse(
            {"error": "Unsupported URL"},
            status_code=400
        )

    # Generate output filename
    output_file = f"/app/{uuid.uuid4()}.mp4"

    # yt-dlp command
    cmd = [
        "yt-dlp",
        "-f", "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[acodec^=mp4a]/b",
        "--merge-output-format", "mp4",
        "--cookies", COOKIE_FILE,
        "-o", output_file,
        url
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False   # do NOT crash backend
        )
    except Exception as e:
        return JSONResponse(
            {"error": "yt-dlp crashed", "details": str(e)},
            status_code=400
        )

    # If yt-dlp failed
    if result.returncode != 0:
        return JSONResponse(
            {
                "error": "Video download failed",
                "stderr": result.stderr[:500],
                "stdout": result.stdout[:500]
            },
            status_code=400      # IMPORTANT: not 500!
        )

    # File exists?
    if not os.path.exists(output_file):
        return JSONResponse(
            {"error": "Download failed – file not created"},
            status_code=400
        )

    # Success → return MP4
    return FileResponse(
        output_file,
        media_type="video/mp4",
        filename="video.mp4"
    )
