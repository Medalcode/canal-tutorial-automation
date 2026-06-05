#!/usr/bin/env python3
"""
FastAPI Backend - Administrador de Videos
Endpoints REST para generación y gestión de videos
"""

import asyncio
import json
import os
import uuid
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI(title="Video Generator Pro", version="1.0")

# Configuración
OUTPUT_DIR = Path("output")
SCRIPTS_DIR = Path("scripts")
JOBS_DIR = Path(".jobs")

for directory in [OUTPUT_DIR, SCRIPTS_DIR, JOBS_DIR]:
    directory.mkdir(exist_ok=True)


# ============ Models ============

class Scene(BaseModel):
    id: str
    title: str
    narration: str
    commands: List[str]


class Script(BaseModel):
    topic: str
    scenes: List[Scene]


class GenerateScriptRequest(BaseModel):
    topic: str
    num_scenes: int = 5

class GenerateVideoRequest(BaseModel):
    upload_to_youtube: bool = False
    youtube_title: Optional[str] = None
    youtube_description: Optional[str] = None
    youtube_tags: Optional[List[str]] = None


class VideoJob(BaseModel):
    job_id: str
    status: str
    script_file: str
    created_at: str
    progress: float = 0.0
    message: str = ""


# ============ Database (JSON files) ============

def load_job(job_id: str) -> Dict:
    job_file = JOBS_DIR / f"{job_id}.json"
    if job_file.exists():
        with open(job_file) as f:
            return json.load(f)
    return None


def save_job(job_id: str, data: Dict):
    job_file = JOBS_DIR / f"{job_id}.json"
    with open(job_file, "w") as f:
        json.dump(data, f, indent=2)


def list_jobs() -> List[Dict]:
    jobs = []
    for job_file in JOBS_DIR.glob("*.json"):
        with open(job_file) as f:
            jobs.append(json.load(f))
    return sorted(jobs, key=lambda x: x["created_at"], reverse=True)


# ============ API Endpoints ============

@app.get("/api/health")
def health_check():
    """Verificar estado del servidor"""
    return {
        "status": "ok",
        "version": "1.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/scripts/generate")
async def generate_script_endpoint(request: GenerateScriptRequest):
    """Generar guión con Gemini IA"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY no configurada. Establécela como variable de entorno."
        )

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
        Eres un experto creador de tutoriales técnicos para YouTube para niños y principiantes.
        Crea un guion estructurado basándote en las siguientes ideas dadas por el usuario:
        "{request.topic}"

        Requisitos:
        - Mínimo {request.num_scenes} secciones
        - Narración clara, motivadora y en español latino
        - Cada escena DEBE tener código Python REAL y funcional en el campo "commands"
        - El código debe ser educativo, bien comentado y mostrar conceptos paso a paso
        - Duración: 8-12 minutos

        Responde SOLO con JSON válido (sin ```json):
        {{
          "topic": "{request.topic}",
          "youtube_title": "Título llamativo para YouTube...",
          "youtube_description": "Descripción optimizada para SEO...",
          "youtube_tags": ["tag1", "tag2", "tag3"],
          "scenes": [
            {{
              "id": "intro",
              "title": "Introducción",
              "narration": "Texto de narración clara...",
              "language": "python",
              "commands": [
                "# Importamos las librerías necesarias\nimport os\nfrom pathlib import Path",
                "def mi_funcion():\n    print('Hola mundo')\n\nmi_funcion()"
              ]
            }}
          ]
        }}
        """

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )

        script_data = json.loads(response.text)
        script_id = str(uuid.uuid4())[:8]
        script_file = SCRIPTS_DIR / f"{script_id}.json"

        with open(script_file, "w", encoding="utf-8") as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "script_id": script_id,
            "topic": script_data["topic"],
            "num_scenes": len(script_data["scenes"]),
            "file": str(script_file)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scripts/{script_id}")
def get_script(script_id: str):
    """Obtener guión completo"""
    script_file = SCRIPTS_DIR / f"{script_id}.json"
    if not script_file.exists():
        raise HTTPException(status_code=404, detail="Script no encontrado")

    with open(script_file) as f:
        return json.load(f)


@app.put("/api/scripts/{script_id}")
def update_script(script_id: str, script: Script):
    """Actualizar guión"""
    script_file = SCRIPTS_DIR / f"{script_id}.json"
    if not script_file.exists():
        raise HTTPException(status_code=404, detail="Script no encontrado")

    with open(script_file, "w") as f:
        json.dump(script.dict(), f, ensure_ascii=False, indent=2)

    return {"success": True, "message": "Script actualizado"}


@app.get("/api/scripts")
def list_scripts():
    """Listar todos los guiones"""
    scripts = []
    for script_file in SCRIPTS_DIR.glob("*.json"):
        with open(script_file) as f:
            data = json.load(f)
            scripts.append({
                "id": script_file.stem,
                "topic": data["topic"],
                "scenes": len(data["scenes"]),
                "created": script_file.stat().st_mtime
            })
    return sorted(scripts, key=lambda x: x["created"], reverse=True)


@app.post("/api/videos/generate")
async def generate_video(
    script_id: str,
    background_tasks: BackgroundTasks,
    request: GenerateVideoRequest = None
):
    """Generar video a partir de guión"""
    if request is None:
        request = GenerateVideoRequest()

    script_file = SCRIPTS_DIR / f"{script_id}.json"
    if not script_file.exists():
        raise HTTPException(status_code=404, detail="Script no encontrado")

    job_id = str(uuid.uuid4())[:12]
    job_data = {
        "job_id": job_id,
        "script_id": script_id,
        "status": "queued",
        "progress": 0,
        "message": "En cola para generar...",
        "created_at": datetime.now().isoformat(),
        "output_files": []
    }
    save_job(job_id, job_data)

    # Ejecutar generación en background
    background_tasks.add_task(
        generate_video_background,
        job_id,
        str(script_file),
        request.upload_to_youtube,
        request.youtube_title,
        request.youtube_description,
        request.youtube_tags
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Video enviado a cola de generación"
    }


async def generate_video_background(
    job_id: str, 
    script_file: str, 
    upload_to_youtube: bool = False,
    youtube_title: str = None,
    youtube_description: str = None,
    youtube_tags: List[str] = None
):
    """Generar video en background"""
    try:
        # Copiar script a script.json para que generate_video.py lo use
        import shutil
        shutil.copy(script_file, "script.json")

        job = load_job(job_id)
        job["status"] = "generating"
        job["progress"] = 10
        job["message"] = "Iniciando generación..."
        save_job(job_id, job)

        # Ejecutar generate_video.py
        process = await asyncio.create_subprocess_exec(
            "python", "generate_video.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            job["status"] = "completed"
            job["progress"] = 100
            job["message"] = "Video generado exitosamente"

            # Listar archivos de output
            output_files = []
            for file in OUTPUT_DIR.glob("*"):
                if file.is_file():
                    output_files.append({
                        "name": file.name,
                        "size": file.stat().st_size,
                        "url": f"/api/files/{file.name}"
                    })

            job["output_files"] = output_files

            if upload_to_youtube:
                job["message"] = "Video generado. Subiendo a YouTube..."
                save_job(job_id, job)
                try:
                    import youtube_uploader
                    video_file_path = str(OUTPUT_DIR / "video_con_musica.mp4")
                    # Llama al script de subida
                    video_url = youtube_uploader.upload_to_youtube(
                        video_file_path, 
                        youtube_title or "Nuevo Tutorial", 
                        youtube_description or "Tutorial generado automáticamente.", 
                        youtube_tags or []
                    )
                    job["message"] = f"¡Subido a YouTube exitosamente! URL: {video_url}"
                except Exception as e:
                    job["status"] = "failed"
                    job["message"] = f"Video creado, pero falló la subida a YouTube: {str(e)}"
                    save_job(job_id, job)
                    return

        else:
            job["status"] = "failed"
            job["progress"] = 0
            # Limitar el mensaje de error a las últimas 3 líneas del stderr para no mostrar todo el log de ffmpeg
            stderr_text = stderr.decode(errors='ignore')
            last_lines = [l for l in stderr_text.strip().splitlines() if l.strip()][-3:]
            job["message"] = f"Error en la generación: {'|'.join(last_lines)}"

    except Exception as e:
        job["status"] = "failed"
        job["message"] = str(e)

    finally:
        save_job(job_id, job)


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """Obtener estado de un job"""
    job = load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return job


@app.get("/api/jobs")
def list_jobs_endpoint():
    """Listar todos los jobs"""
    return list_jobs()


@app.get("/api/files/{filename}")
def download_file(filename: str):
    """Descargar archivo de output"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@app.get("/api/files")
def list_files():
    """Listar archivos generados"""
    files = []
    for file in OUTPUT_DIR.glob("*"):
        if file.is_file():
            files.append({
                "name": file.name,
                "size": file.stat().st_size,
                "modified": file.stat().st_mtime,
                "url": f"/api/files/{file.name}"
            })
    return sorted(files, key=lambda x: x["modified"], reverse=True)


@app.delete("/api/files/{filename}")
def delete_file(filename: str):
    """Eliminar archivo"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    file_path.unlink()
    return {"success": True, "message": f"{filename} eliminado"}


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    """Eliminar job"""
    job_file = JOBS_DIR / f"{job_id}.json"
    if not job_file.exists():
        raise HTTPException(status_code=404, detail="Job no encontrado")

    job_file.unlink()
    return {"success": True, "message": "Job eliminado"}


# ============ Static Files ============

# Montar archivos estáticos (frontend)
app.mount("/", StaticFiles(directory="web", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Video Generator Pro...")
    print("📊 API disponible en: http://localhost:8000/api")
    print("🌐 Frontend en: http://localhost:8000")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
