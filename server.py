from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import subprocess, uuid, os, json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
OUT = "outputs"
os.makedirs(OUT, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def home():
    return open("static/index.html", encoding="utf-8").read()

@app.post("/make")
def make(url: str = Form(...), clips: int = Form(5), seconds: int = Form(45)):
    job = str(uuid.uuid4())[:8]
    folder = os.path.join(OUT, job)
    os.makedirs(folder, exist_ok=True)
    src = os.path.join(folder, "source.mp4")
    try:
        subprocess.run([
            "yt-dlp", "-f", "bv*+ba/b", "--merge-output-format", "mp4",
            "-o", src, url
        ], check=True, timeout=1800)
        dur = float(subprocess.check_output([
            "ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=noprint_wrappers=1:nokey=1",src
        ]))
        length = min(seconds, max(10, dur/clips))
        results=[]
        for i in range(clips):
            start=max(0, (dur-length)*i/max(1,clips-1))
            out=os.path.join(folder,f"short_{i+1}.mp4")
            subprocess.run([
                "ffmpeg","-y","-ss",str(start),"-i",src,"-t",str(length),
                "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,"
                      "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
                "-c:v","libx264","-preset","veryfast","-c:a","aac",out
            ], check=True, timeout=1200)
            results.append("/"+out)
        return {"ok":True,"clips":results}
    except Exception as e:
        return JSONResponse({"ok":False,"error":str(e)}, status_code=500)
