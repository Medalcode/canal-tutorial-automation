#!/usr/bin/env python3
"""
FastAPI Backend - Administrador de Videos
Endpoints REST para generación y gestión de videos
"""

import asyncio
import json
import os
import uuid
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Video Generator Pro", version="1.0")

# Configuración
OUTPUT_DIR = Path("output")
SCRIPTS_DIR = Path("scripts")
DB_PATH = "database.sqlite"

for directory in [OUTPUT_DIR, SCRIPTS_DIR]:
    directory.mkdir(exist_ok=True)

# ============ Database (SQLite) ============

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            script_id TEXT,
            status TEXT,
            progress INTEGER,
            message TEXT,
            created_at TEXT,
            output_files TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def load_job(job_id: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jobs WHERE job_id = ?', (job_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        job_data = dict(row)
        job_data["output_files"] = json.loads(job_data["output_files"]) if job_data["output_files"] else []
        return job_data
    return None

def save_job(job_id: str, data: Dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    output_files_str = json.dumps(data.get("output_files", []))
    cursor.execute('''
        INSERT INTO jobs (job_id, script_id, status, progress, message, created_at, output_files)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
            status=excluded.status,
            progress=excluded.progress,
            message=excluded.message,
            output_files=excluded.output_files
    ''', (
        data.get("job_id"), data.get("script_id"), data.get("status"), 
        data.get("progress", 0), data.get("message"), data.get("created_at"), 
        output_files_str
    ))
    conn.commit()
    conn.close()

def list_jobs() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    jobs = []
    for row in rows:
        job_data = dict(row)
        job_data["output_files"] = json.loads(job_data["output_files"]) if job_data["output_files"] else []
        jobs.append(job_data)
    return jobs

def delete_job_db(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM jobs WHERE job_id = ?', (job_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# ============ Middleware / Auth ============

API_SECRET = os.getenv("API_SECRET_TOKEN", "")

def verify_token(x_api_token: Optional[str] = Header(None)):
    if API_SECRET and x_api_token != API_SECRET:
        raise HTTPException(status_code=401, detail="Token inválido o no proporcionado")
    return True

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

# ============ API Endpoints ============

@app.get("/api/health")
def health_check():
    """Verificar estado del servidor"""
    return {
        "status": "ok",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "database": "sqlite"
    }


@app.post("/api/scripts/generate")
async def generate_script_endpoint(request: GenerateScriptRequest, auth: bool = Depends(verify_token)):
    """Generar guión con Gemini IA"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY no configurada. Establécela como variable de entorno."
        )

    try:
        prompt = f"""
        Eres un experto creador de tutoriales técnicos para YouTube para niños y principiantes.
        Crea un guion estructurado basándote en las siguientes ideas dadas por el usuario:
        "{request.topic}"

        Requisitos:
        - Mínimo {request.num_scenes} secciones
        - Narración clara, motivadora y en español latino
        - Cada escena DEBE tener código REAL y funcional en el campo "commands"
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

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            )
        )

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]

        script_data = json.loads(text)
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scripts/{script_id}")
def get_script(script_id: str, auth: bool = Depends(verify_token)):
    script_file = SCRIPTS_DIR / f"{script_id}.json"
    if not script_file.exists():
        raise HTTPException(status_code=404, detail="Script no encontrado")

    with open(script_file) as f:
        return json.load(f)


@app.put("/api/scripts/{script_id}")
def update_script(script_id: str, script: Script, auth: bool = Depends(verify_token)):
    script_file = SCRIPTS_DIR / f"{script_id}.json"
    if not script_file.exists():
        raise HTTPException(status_code=404, detail="Script no encontrado")

    with open(script_file, "w", encoding="utf-8") as f:
        json.dump(script.dict(), f, ensure_ascii=False, indent=2)

    return {"success": True, "message": "Script actualizado"}


@app.get("/api/scripts")
def list_scripts(auth: bool = Depends(verify_token)):
    scripts = []
    for script_file in SCRIPTS_DIR.glob("*.json"):
        with open(script_file) as f:
            data = json.load(f)
            scripts.append({
                "id": script_file.stem,
                "topic": data.get("topic", "Sin Título"),
                "scenes": len(data.get("scenes", [])),
                "created": script_file.stat().st_mtime
            })
    return sorted(scripts, key=lambda x: x["created"], reverse=True)


@app.post("/api/videos/generate")
async def generate_video(
    script_id: str,
    background_tasks: BackgroundTasks,
    request: GenerateVideoRequest = None,
    auth: bool = Depends(verify_token)
):
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
    try:
        job = load_job(job_id)
        job["status"] = "generating"
        job["progress"] = 10
        job["message"] = "Iniciando generación (Python)..."
        save_job(job_id, job)

        # Ejecutar generate_video.py pasando script via argumento CLI
        process = await asyncio.create_subprocess_exec(
            "python", "generate_video.py",
            "--script", script_file,
            "--job-id", job_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            job["status"] = "completed"
            job["progress"] = 100
            job["message"] = "Video generado exitosamente"

            # Actualizar output_files del job especificos de este job_id
            output_files = []
            for ext, name in [(".mp4", "Video Final"), (".mp3", "Audio Narracion"), (".png", "Miniatura")]:
                # Buscamos coincidencias con job_id
                for file in OUTPUT_DIR.glob(f"*{job_id}*{ext}"):
                    output_files.append({
                        "name": file.name,
                        "size": file.stat().st_size,
                        "url": f"/api/files/{file.name}",
                        "type": name
                    })

            job["output_files"] = output_files

            if upload_to_youtube:
                job["message"] = "Video generado. Subiendo a YouTube..."
                save_job(job_id, job)
                try:
                    import youtube_uploader
                    final_video_path = OUTPUT_DIR / f"video_con_musica_{job_id}.mp4"
                    video_url = youtube_uploader.upload_to_youtube(
                        str(final_video_path), 
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
            stderr_text = stderr.decode(errors='ignore')
            last_lines = [l for l in stderr_text.strip().splitlines() if l.strip()][-3:]
            job["message"] = f"Error en la generación: {'|'.join(last_lines)}"

    except Exception as e:
        if job := load_job(job_id):
            job["status"] = "failed"
            job["message"] = str(e)

    finally:
        if job := load_job(job_id):
            save_job(job_id, job)


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str, auth: bool = Depends(verify_token)):
    job = load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return job


@app.get("/api/jobs")
def list_jobs_endpoint(auth: bool = Depends(verify_token)):
    return list_jobs()


@app.get("/api/files/{filename}")
def download_file(filename: str, auth: bool = Depends(verify_token)):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@app.get("/api/files")
def list_files(auth: bool = Depends(verify_token)):
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
def delete_file(filename: str, auth: bool = Depends(verify_token)):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    file_path.unlink()
    return {"success": True, "message": f"{filename} eliminado"}


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, auth: bool = Depends(verify_token)):
    if delete_job_db(job_id):
        return {"success": True, "message": "Job eliminado"}
    raise HTTPException(status_code=404, detail="Job no encontrado")


# ============ Static Files ============

app.mount("/", StaticFiles(directory="web", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Video Generator Pro...")
    print("📊 API disponible en: http://localhost:8001/api")
    print("🌐 Frontend en: http://localhost:8001")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8001, reload=True)
