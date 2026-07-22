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
    num_frames: Optional[int] = 97
    num_inference_steps: Optional[int] = 30

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
    num_frames: int = Form(97),
    num_inference_steps: int = Form(30)
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

@app.get("/jobs")
async def list_jobs():
    return {"jobs": list(jobs.values())}
