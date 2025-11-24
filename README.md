# sstube-backend-pro (FastAPI + yt-dlp)

Supports:
- YouTube
- TikTok
- Instagram
- Facebook
- Twitter / X
- MP4 + MP3
- Quality selection: 360 / 480 / 720 / 1080 / best
- Simple in-memory rate limiting

## Endpoints

### GET /
Health check:
  https://your-app.up.railway.app/

### GET /download
Download video or audio:
  https://your-app.up.railway.app/download?url=VIDEO_URL&format=mp4&quality=720
