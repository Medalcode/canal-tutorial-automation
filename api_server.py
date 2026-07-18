#!/usr/bin/env python3

import asyncio
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from logger import get_logger

log = get_logger("api_server")

load_dotenv()

app = FastAPI(title="Video Generator Pro", version="1.0")

OUTPUT_DIR = Path("output")
SCRIPTS_DIR = Path("scripts")
DB_PATH = "database.sqlite"

for directory in [OUTPUT_DIR, SCRIPTS_DIR]:
    directory.mkdir(exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    log.warning("GEMINI_API_KEY no configurada. El endpoint /api/scripts/generate fallara.")

API_SECRET = os.getenv("API_SECRET_TOKEN", "")
if not API_SECRET:
    log.info("API_SECRET_TOKEN no configurado. La API no requiere autenticacion.")

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
    log.info("Base de datos inicializada")

init_db()

def load_job(job_id: str) -> dict | None:
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

def save_job(_job_id: str, data: dict):
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

def list_jobs() -> list[dict]:
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

def verify_token(x_api_token: str | None = Header(None)):
    if API_SECRET and x_api_token != API_SECRET:
        raise HTTPException(status_code=401, detail="Token invalido o no proporcionado")
    return True

# ============ Models ============

class Scene(BaseModel):
    id: str
    title: str
    narration: str
    commands: list[str]

class Script(BaseModel):
    topic: str
    scenes: list[Scene]

class GenerateScriptRequest(BaseModel):
    topic: str
    num_scenes: int = 5

class GenerateVideoRequest(BaseModel):
    upload_to_youtube: bool = False
    youtube_title: str | None = None
    youtube_description: str | None = None
    youtube_tags: list[str] | None = None

# ============ API Endpoints ============

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "database": "sqlite"
    }


@app.post("/api/scripts/generate")
async def generate_script_endpoint(request: GenerateScriptRequest, _auth: bool = Depends(verify_token)):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY no configurada. Establecela como variable de entorno."
        )

    try:
        prompt = f"""
        Eres un experto creador de tutoriales tecnicos para YouTube para ninos y principiantes.
        Crea un guion estructurado basandote en las siguientes ideas dadas por el usuario:
        "{request.topic}"

        Requisitos:
        - Minimo {request.num_scenes} secciones
        - Narracion clara, motivadora y en espanol latino
        - Cada escena DEBE incluir animaciones didacticas escritas con Manim en el campo "manim_code".
        - El codigo de Manim debe definir una clase `SceneAnim(Scene)` e importar `from manim import *`. No incluyas comandos de sistema operativo como `!manim`.
        - Manten las animaciones simples pero profesionales (ej. diagramas de flujo, revelacion de codigo, formulas matematicas, graficos basicos).
        - El campo "commands" puede quedar como un arreglo vacio [] o tener codigo de consola basico de respaldo.
        - Duracion: 8-12 minutos

        Responde SOLO con JSON valido (sin ```json):
        {{{{
          "topic": "{request.topic}",
          "youtube_title": "Titulo llamativo para YouTube...",
          "youtube_description": "Descripcion optimizada para SEO...",
          "youtube_tags": ["tag1", "tag2", "tag3"],
          "scenes": [
            {{{{
              "id": "intro",
              "title": "Introduccion",
              "narration": "Texto de narracion clara...",
              "language": "python",
              "commands": [
                "# Opcional: codigo para terminal de fallback",
                "print('Fallback')"
              ],
              "manim_code": "from manim import *\\n\\nclass SceneAnim(Scene):\\n    def construct(self):\\n        text = Text('¡Hola a todos!', color=WHITE)\\n        self.play(Write(text))\\n        self.wait(1)"
            }}}}
          ]
        }}}}
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

        log.info(f"Script generado: {script_id} - tema: {request.topic}")

        return {
            "success": True,
            "script_id": script_id,
            "topic": script_data["topic"],
            "num_scenes": len(script_data["scenes"]),
            "file": str(script_file)
        }

    except Exception as e:
        log.exception(f"Error generando script: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/scripts/{script_id}")
def get_script(script_id: str, _auth: bool = Depends(verify_token)):
    script_file = SCRIPTS_DIR / f"{script_id}.json"
    if not script_file.exists():
        raise HTTPException(status_code=404, detail="Script no encontrado")

    with open(script_file) as f:
        return json.load(f)


@app.put("/api/scripts/{script_id}")
def update_script(script_id: str, script: Script, _auth: bool = Depends(verify_token)):
    script_file = SCRIPTS_DIR / f"{script_id}.json"
    if not script_file.exists():
        raise HTTPException(status_code=404, detail="Script no encontrado")

    with open(script_file, "w", encoding="utf-8") as f:
        json.dump(script.dict(), f, ensure_ascii=False, indent=2)

    log.info(f"Script actualizado: {script_id}")
    return {"success": True, "message": "Script actualizado"}


@app.get("/api/scripts")
def list_scripts(_auth: bool = Depends(verify_token)):
    scripts = []
    for script_file in SCRIPTS_DIR.glob("*.json"):
        with open(script_file) as f:
            data = json.load(f)
            scripts.append({
                "id": script_file.stem,
                "topic": data.get("topic", "Sin Titulo"),
                "scenes": len(data.get("scenes", [])),
                "created": script_file.stat().st_mtime
            })
    return sorted(scripts, key=lambda x: x["created"], reverse=True)


@app.post("/api/videos/generate")
async def generate_video(
    script_id: str,
    background_tasks: BackgroundTasks,
    request: GenerateVideoRequest = None,
    _auth: bool = Depends(verify_token)
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

    log.info(f"Job encolado: {job_id} para script {script_id}")
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Video enviado a cola de generacion"
    }


async def generate_video_background(
    job_id: str,
    script_file: str,
    upload_to_youtube: bool = False,
    youtube_title: str = None,
    youtube_description: str = None,
    youtube_tags: list[str] = None
):
    job = None
    try:
        job = load_job(job_id)
        job["status"] = "generating"
        job["progress"] = 10
        job["message"] = "Iniciando generacion..."
        save_job(job_id, job)

        python_exe = sys.executable or "python"
        log.info(f"Ejecutando: {python_exe} generate_video.py --script {script_file} --job-id {job_id}")

        process = await asyncio.create_subprocess_exec(
            python_exe, "generate_video.py",
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

            output_files = []
            for ext, name in [(".mp4", "Video Final"), (".mp3", "Audio Narracion"), (".png", "Miniatura")]:
                for file in OUTPUT_DIR.glob(f"*{job_id}*{ext}"):
                    output_files.append({
                        "name": file.name,
                        "size": file.stat().st_size,
                        "url": f"/api/files/{file.name}",
                        "type": name
                    })

            job["output_files"] = output_files
            log.info(f"Job {job_id} completado. Archivos: {[f['name'] for f in output_files]}")

            if upload_to_youtube:
                job["message"] = "Video generado. Subiendo a YouTube..."
                save_job(job_id, job)
                try:
                    import youtube_uploader
                    final_video_path = OUTPUT_DIR / f"video_con_musica_{job_id}.mp4"
                    video_url = youtube_uploader.upload_to_youtube(
                        str(final_video_path),
                        youtube_title or "Nuevo Tutorial",
                        youtube_description or "Tutorial generado automaticamente.",
                        youtube_tags or []
                    )
                    job["message"] = f"Subido a YouTube exitosamente! URL: {video_url}"
                    log.info(f"Video {job_id} subido a YouTube: {video_url}")
                except Exception as e:
                    job["status"] = "failed"
                    job["message"] = f"Video creado, pero fallo la subida a YouTube: {str(e)}"
                    log.error(f"Error subiendo video {job_id} a YouTube: {e}")
                    save_job(job_id, job)
                    return
        else:
            job["status"] = "failed"
            job["progress"] = 0
            stderr_text = stderr.decode(errors='ignore')
            last_lines = [line for line in stderr_text.strip().splitlines() if line.strip()][-3:]
            job["message"] = f"Error en la generacion: {'|'.join(last_lines)}"
            log.error(f"Job {job_id} fallo. stderr: {stderr_text[:500]}")

    except Exception as e:
        log.exception(f"Error en generate_video_background para job {job_id}: {e}")
        if job:
            job["status"] = "failed"
            job["message"] = str(e)

    finally:
        if job:
            save_job(job_id, job)


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str, _auth: bool = Depends(verify_token)):
    job = load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return job


@app.get("/api/jobs")
def list_jobs_endpoint(_auth: bool = Depends(verify_token)):
    return list_jobs()


@app.get("/api/files/{filename}")
def download_file(filename: str, _auth: bool = Depends(verify_token)):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@app.get("/api/files")
def list_files(_auth: bool = Depends(verify_token)):
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
def delete_file(filename: str, _auth: bool = Depends(verify_token)):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    file_path.unlink()
    log.info(f"Archivo eliminado: {filename}")
    return {"success": True, "message": f"{filename} eliminado"}


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, _auth: bool = Depends(verify_token)):
    if delete_job_db(job_id):
        log.info(f"Job eliminado: {job_id}")
        return {"success": True, "message": "Job eliminado"}
    raise HTTPException(status_code=404, detail="Job no encontrado")


app.mount("/", StaticFiles(directory="web", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    log.info("Iniciando Video Generator Pro...")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8001, reload=True)
