import os
import uuid
import json
import asyncio
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

APP_DIR = "/tmp/sstube"
MAX_DURATION = 60 * 30  # 30 minutes

os.makedirs(APP_DIR, exist_ok=True)

app = FastAPI()

# 🔒 CORS – allow only your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sstube.pro",
        "https://www.sstube.pro"
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# -----------------------
# ROOT (REQUIRED BY RAILWAY)
# -----------------------
@app.get("/")
def root():
    return {"status": "running"}

# -----------------------
# HEALTH
# -----------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -----------------------
# META
# -----------------------
@app.get("/meta")
async def meta(url: str = Query(...)):
    try:
        cmd = ["yt-dlp", "--dump-json", "--no-playlist", url]
        p = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await p.communicate()

        if p.returncode != 0:
            return JSONResponse({"error": err.decode()}, status_code=400)

        info = json.loads(out.decode())
        duration = info.get("duration", 0)

        if duration and duration > MAX_DURATION:
            return JSONResponse({"error": "Video too long"}, status_code=400)

        return {
            "status": "ok",
            "meta": {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "author": info.get("uploader"),
                "duration": duration,
                "platform": info.get("extractor_key"),
            },
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

# -----------------------
# CLEANUP
# -----------------------
async def cleanup(path: str):
    try:
        os.remove(path)
    except:
        pass

# -----------------------
# MP4 DOWNLOAD
# -----------------------
@app.get("/download")
async def download(url: str = Query(...)):
    out = f"{APP_DIR}/{uuid.uuid4()}.mp4"

    cmd = [
        "yt-dlp",
        "-f", "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", out,
        url,
    ]

    p = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await p.communicate()

    if p.returncode != 0 or not os.path.exists(out):
        return JSONResponse({"error": err.decode()}, status_code=400)

    return FileResponse(
        out,
        media_type="video/mp4",
        filename="video.mp4",
        background=cleanup(out),
    )

# -----------------------
# MP3 DOWNLOAD
# -----------------------
@app.get("/mp3")
async def mp3(url: str = Query(...)):
    out = f"{APP_DIR}/{uuid.uuid4()}.mp3"

    cmd = [
    "yt-dlp",
    "-f", "ba",
    "-x",
    "--audio-format", "mp3",
    "--audio-quality", "192K",
    "--no-playlist",
    "--postprocessor-args", "ffmpeg:-vn",
    "-o", out,
    url,
]

    p = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await p.communicate()

    if p.returncode != 0 or not os.path.exists(out):
        return JSONResponse({"error": err.decode()}, status_code=400)

    return FileResponse(
        out,
        media_type="audio/mpeg",
        filename="audio.mp3",
        background=cleanup(out),
    )
