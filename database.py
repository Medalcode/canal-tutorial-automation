import json
import sqlite3
from logger import get_logger

log = get_logger("database")
DB_PATH = "database.sqlite"

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
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

def load_job(job_id: str, db_path=DB_PATH) -> dict | None:
    conn = sqlite3.connect(db_path)
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

def save_job(_job_id: str, data: dict, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
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

def list_jobs(db_path=DB_PATH) -> list[dict]:
    conn = sqlite3.connect(db_path)
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

def delete_job_db(job_id: str, db_path=DB_PATH) -> bool:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM jobs WHERE job_id = ?', (job_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
