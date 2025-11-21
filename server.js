import express from "express";
import cors from "cors";
import { exec } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const app = express();
app.use(cors());
app.use(express.json());

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function runCmd(cmd) {
    return new Promise((resolve, reject) => {
        exec(cmd, { maxBuffer: 1024 * 1024 * 20 }, (err, stdout, stderr) => {
            if (err) {
                return reject(stderr || err.message);
            }
            resolve(stdout);
        });
    });
}

// =======================
// GET VIDEO INFORMATION
// =======================
app.get("/api/info", async (req, res) => {
    const url = req.query.url;
    if (!url) return res.json({ error: "Missing URL" });

    try {
        const cmd = `yt-dlp -J --no-warnings --force-ipv4 --extractor-args "youtube:player_client=default" "${url}"`;
        const output = await runCmd(cmd);

        const info = JSON.parse(output);
        if (!info || !info.formats) {
            return res.json({ error: "No formats available" });
        }

        return res.json({
            title: info.title,
            thumbnail: info.thumbnail,
            formats: info.formats
        });

    } catch (err) {
        return res.json({
            error: "Failed to fetch info",
            details: err.toString()
        });
    }
});

// =======================
// MP3 DOWNLOAD
// =======================
app.get("/api/audio", async (req, res) => {
    const url = req.query.url;
    if (!url) return res.json({ error: "Missing URL" });

    res.setHeader("Content-Type", "audio/mpeg");
    res.setHeader("Content-Disposition", "attachment; filename=audio.mp3");

    const cmd = `yt-dlp -f bestaudio --extractor-args "youtube:player_client=default" -o - "${url}" | ffmpeg -i pipe:0 -vn -acodec libmp3lame -b:a 192k -f mp3 pipe:1`;

    const process = exec(cmd, { maxBuffer: 1024 * 1024 * 100 });

    process.stdout.pipe(res);

    process.stderr.on("data", (d) => console.log("ffmpeg:", d.toString()));
});

// =======================
// MP4 DOWNLOAD (MERGED)
// =======================
app.get("/api/video", async (req, res) => {
    const url = req.query.url;
    const quality = req.query.quality || "1080";

    if (!url) return res.json({ error: "Missing URL" });

    const videoFormat = {
        "1080": "bestvideo[height<=1080]+bestaudio",
        "720": "bestvideo[height<=720]+bestaudio",
        "480": "bestvideo[height<=480]+bestaudio"
    }[quality] || "bestvideo+bestaudio";

    res.setHeader("Content-Type", "video/mp4");
    res.setHeader("Content-Disposition", `attachment; filename=video_${quality}.mp4`);

    const cmd = `
        yt-dlp -f "${videoFormat}" --extractor-args "youtube:player_client=default" -o - "${url}" \
        | ffmpeg -i pipe:0 -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k -f mp4 pipe:1
    `;

    const process = exec(cmd, { maxBuffer: 1024 * 1024 * 200 });
    process.stdout.pipe(res);

    process.stderr.on("data", d => console.log("ffmpeg:", d.toString()));
});

// =======================
// ROOT
// =======================
app.get("/", (req, res) => {
    res.send("SSTube Backend by Render");
});


// =======================
// START SERVER
// =======================
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
    console.log("Backend running on port " + PORT);
});
