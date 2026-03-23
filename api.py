"""
Nga J1 Pipeline — FastAPI backend
Serves the static frontend + API backed by SQLite
Port: 4005
"""
import sqlite3, os, json
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "pipeline.db"
RESUME_DIR = Path("/workspace/group/candidates/mynga/resumes/output")

app = FastAPI(docs_url=None, redoc_url=None)

# ── DB SETUP ─────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS company_state (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'not-contacted',
            notes TEXT NOT NULL DEFAULT '',
            last_contacted TEXT,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS outreach_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            action TEXT NOT NULL,
            body TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ── MODELS ────────────────────────────────────────────────────────────────────

class CompanyUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    last_contacted: Optional[str] = None

class OutreachEntry(BaseModel):
    company_id: str
    action: str           # 'emailed' | 'called' | 'linkedin' | 'responded' | 'met'
    body: Optional[str] = None

# ── API ROUTES ────────────────────────────────────────────────────────────────

@app.get("/api/state")
def get_state():
    """Return all company states as {id: {status, notes, last_contacted}}"""
    conn = get_db()
    rows = conn.execute("SELECT * FROM company_state").fetchall()
    conn.close()
    return {r["id"]: {
        "status": r["status"],
        "notes": r["notes"],
        "last_contacted": r["last_contacted"],
        "updated_at": r["updated_at"],
    } for r in rows}

@app.patch("/api/companies/{company_id}")
def update_company(company_id: str, update: CompanyUpdate):
    conn = get_db()
    now = datetime.utcnow().isoformat()
    # Upsert
    conn.execute("""
        INSERT INTO company_state (id, status, notes, last_contacted, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            status = COALESCE(excluded.status, status),
            notes = COALESCE(excluded.notes, notes),
            last_contacted = COALESCE(excluded.last_contacted, last_contacted),
            updated_at = excluded.updated_at
    """, (
        company_id,
        update.status or "not-contacted",
        update.notes or "",
        update.last_contacted,
        now,
    ))
    conn.commit()
    row = conn.execute("SELECT * FROM company_state WHERE id=?", (company_id,)).fetchone()
    conn.close()
    return dict(row)

@app.get("/api/companies/{company_id}")
def get_company(company_id: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM company_state WHERE id=?", (company_id,)).fetchone()
    conn.close()
    if not row:
        return {"id": company_id, "status": "not-contacted", "notes": "", "last_contacted": None}
    return dict(row)

@app.post("/api/outreach")
def log_outreach(entry: OutreachEntry):
    conn = get_db()
    conn.execute(
        "INSERT INTO outreach_log (company_id, action, body) VALUES (?, ?, ?)",
        (entry.company_id, entry.action, entry.body)
    )
    # Auto-update company status when outreach is logged
    if entry.action in ("emailed", "linkedin", "called"):
        conn.execute("""
            INSERT INTO company_state (id, status, last_contacted, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                status = 'emailed',
                last_contacted = datetime('now'),
                updated_at = datetime('now')
        """, (entry.company_id, "emailed", datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/api/outreach")
def get_outreach(company_id: Optional[str] = None):
    conn = get_db()
    if company_id:
        rows = conn.execute(
            "SELECT * FROM outreach_log WHERE company_id=? ORDER BY created_at DESC",
            (company_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM outreach_log ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/stats")
def get_stats():
    conn = get_db()
    rows = conn.execute("SELECT status, COUNT(*) as n FROM company_state GROUP BY status").fetchall()
    conn.close()
    counts = {r["status"]: r["n"] for r in rows}
    return counts

@app.get("/api/resumes/{filename}")
def get_resume(filename: str):
    path = RESUME_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(path)

@app.get("/api/health")
def health():
    return {"ok": True}

# ── STATIC FILES + SPA FALLBACK ──────────────────────────────────────────────

app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")
