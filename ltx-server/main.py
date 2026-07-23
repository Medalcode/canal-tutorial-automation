import os
import uuid
import torch
from fastapi import FastAPI, BackgroundTasks, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional
from inference import LTXInference
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LTX Video Inference API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = "/app/output"
# Fallback for local testing outside docker
if not os.path.exists("/app"):
    OUTPUT_DIR = "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Global inference engine
ltx_engine = LTXInference()

# Simple in-memory job tracker
jobs: Dict[str, dict] = {}

class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = "worst quality, inconsistent motion, blurry, jittery, distorted"
    width: Optional[int] = 512
    height: Optional[int] = 320
    num_frames: Optional[int] = 49
    num_inference_steps: Optional[int] = 25

class ComposeRequest(BaseModel):
    job_id: str
    code_text: Optional[str] = "# Code Example\nimport torch\n\ndef main():\n    print('40/60 Split Tutorial Completed!')"
    narration_text: Optional[str] = "Hola a todos, hoy aprenderemos cómo crear un script en Python para automatización."

def process_t2v_job(job_id: str, request: GenerateRequest):
    jobs[job_id]["status"] = "processing"
    output_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
    try:
        ltx_engine.generate_video(
            prompt=request.prompt,
            output_path=output_path,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_frames=request.num_frames,
            num_inference_steps=request.num_inference_steps
        )
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["file_path"] = output_path
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

def process_i2v_job(job_id: str, image_path: str, prompt: str, negative_prompt: str, width: int, height: int, num_frames: int, num_inference_steps: int):
    jobs[job_id]["status"] = "processing"
    output_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
    try:
        ltx_engine.generate_video_from_image(
            image_path=image_path,
            prompt=prompt,
            output_path=output_path,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps
        )
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["file_path"] = output_path
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
    finally:
        # Clean up uploaded image
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass

@app.get("/health")
async def health_check():
    return {"status": "ok", "gpu_available": torch.cuda.is_available()}

@app.post("/generate")
async def generate_t2v(request: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "id": job_id,
        "type": "text-to-video",
        "status": "queued",
        "prompt": request.prompt
    }
    background_tasks.add_task(process_t2v_job, job_id, request)
    return {"job_id": job_id, "status": "queued"}

@app.post("/generate/i2v")
async def generate_i2v(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    prompt: str = Form(...),
    negative_prompt: str = Form("worst quality, inconsistent motion, blurry, jittery, distorted"),
    width: int = Form(512),
    height: int = Form(320),
    num_frames: int = Form(49),
    num_inference_steps: int = Form(25)
):
    job_id = str(uuid.uuid4())
    
    # Save uploaded image temporarily
    image_path = os.path.join(OUTPUT_DIR, f"{job_id}_input.png")
    with open(image_path, "wb") as buffer:
        buffer.write(await image.read())
        
    jobs[job_id] = {
        "id": job_id,
        "type": "image-to-video",
        "status": "queued",
        "prompt": prompt
    }
    
    background_tasks.add_task(
        process_i2v_job, 
        job_id, 
        image_path, 
        prompt, 
        negative_prompt, 
        width, 
        height, 
        num_frames, 
        num_inference_steps
    )
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/download/{job_id}")
async def download_video(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Video not ready. Current status: {job['status']}")
        
    return FileResponse(
        path=job["file_path"], 
        media_type="video/mp4", 
        filename=f"{job_id}.mp4"
    )

@app.post("/compose")
async def compose_split_screen(request: ComposeRequest):
    import subprocess
    from code_renderer import render_vscode_ide
    
    avatar_video = None
    if request.job_id and request.job_id in jobs and jobs[request.job_id]["status"] == "completed":
        avatar_video = jobs[request.job_id]["file_path"]
        
    if not avatar_video or not os.path.exists(avatar_video):
        # Fallback to official Ghibli Programmer avatar
        if os.path.exists("/app/ghibli_programmer.png"):
            avatar_video = "/app/ghibli_programmer.png"
        elif os.path.exists("/app/assets/ghibli_programmer.png"):
            avatar_video = "/app/assets/ghibli_programmer.png"
        elif os.path.exists("./assets/ghibli_programmer.png"):
            avatar_video = "./assets/ghibli_programmer.png"
        else:
            raise HTTPException(status_code=400, detail="Avatar base image not found")
        
    split_job_id = f"split_{uuid.uuid4().hex[:8]}"
    final_output_path = os.path.join(OUTPUT_DIR, f"{split_job_id}.mp4")
    
    # 1. Render Code IDE Image (1152x1080)
    code_png_path = os.path.join(OUTPUT_DIR, f"{split_job_id}_code.png")
    img = render_vscode_ide(request.code_text, width=1152, height=1080)
    img.save(code_png_path)
    
    # 2. Render Narration TTS Audio
    narration_mp3_path = os.path.join(OUTPUT_DIR, f"{split_job_id}_narration.mp3")
    cmd_tts = ["edge-tts", "--voice", "es-MX-DaliaNeural", "--text", request.narration_text, "--write-media", narration_mp3_path]
    try:
        subprocess.run(cmd_tts, check=True)
    except Exception as e:
        print(f"Error generating TTS: {e}")
        
    # 3. FFmpeg 40/60 Split-Screen Composite
    is_image = avatar_video.lower().endswith(('.png', '.jpg', '.jpeg'))
    avatar_loop_arg = ["-loop", "1"] if is_image else ["-stream_loop", "-1"]

    duration = 10.0
    if os.path.exists(narration_mp3_path):
        try:
            probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", narration_mp3_path]
            res = subprocess.run(probe_cmd, capture_output=True, text=True)
            duration = float(res.stdout.strip())
        except Exception as e:
            print(f"Could not probe narration duration: {e}")
            duration = 10.0

    if os.path.exists(narration_mp3_path):
        cmd_ffmpeg = [
            "ffmpeg", "-y"
        ] + avatar_loop_arg + [
            "-i", avatar_video,
            "-loop", "1", "-i", code_png_path,
            "-i", narration_mp3_path,
            "-t", str(duration),
            "-filter_complex", "[0:v]scale=768:1080:force_original_aspect_ratio=increase,crop=768:1080[left]; [1:v]scale=1152:1080[right]; [left][right]hstack=inputs=2[v]",
            "-map", "[v]", "-map", "2:a",
            "-c:v", "libx264", "-preset", "ultrafast", "-b:v", "5M",
            "-c:a", "aac",
            final_output_path
        ]
    else:
        cmd_ffmpeg = [
            "ffmpeg", "-y"
        ] + avatar_loop_arg + [
            "-i", avatar_video,
            "-loop", "1", "-i", code_png_path,
            "-t", "10",
            "-filter_complex", "[0:v]scale=768:1080:force_original_aspect_ratio=increase,crop=768:1080[left]; [1:v]scale=1152:1080[right]; [left][right]hstack=inputs=2[v]",
            "-map", "[v]",
            "-c:v", "libx264", "-preset", "ultrafast", "-b:v", "5M",
            final_output_path
        ]
        
    try:
        subprocess.run(cmd_ffmpeg, check=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg composite failed: {e}")
        
    jobs[split_job_id] = {
        "id": split_job_id,
        "type": "split-composite",
        "status": "completed",
        "file_path": final_output_path
    }
    
    return {"job_id": split_job_id, "status": "completed", "file_path": final_output_path}

@app.get("/jobs")
async def list_jobs():
    return {"jobs": list(jobs.values())}
