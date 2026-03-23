"""
Nga J1 Pipeline — FastAPI backend
Serves the static frontend + API backed by SQLite + companies.json
Port: 4005
"""
import sqlite3, json
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "pipeline.db"
COMPANIES_PATH = BASE_DIR / "data" / "companies.json"
RESUME_DIR = Path("/workspace/group/candidates/mynga/resumes/output")

app = FastAPI(docs_url=None, redoc_url=None)

# ── DB SETUP ──────────────────────────────────────────────────────────────────

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

# ── HELPERS ───────────────────────────────────────────────────────────────────

def load_companies():
    with open(COMPANIES_PATH) as f:
        return json.load(f)

def get_all_state():
    conn = get_db()
    rows = conn.execute("SELECT * FROM company_state").fetchall()
    conn.close()
    return {r["id"]: dict(r) for r in rows}

# ── MODELS ────────────────────────────────────────────────────────────────────

class CompanyUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    last_contacted: Optional[str] = None

class OutreachEntry(BaseModel):
    company_id: str
    action: str  # 'emailed' | 'called' | 'linkedin' | 'responded' | 'met'
    body: Optional[str] = None

# ── API ROUTES ────────────────────────────────────────────────────────────────

@app.get("/api/companies")
def get_companies():
    """Full company list from JSON merged with live DB state."""
    companies = load_companies()
    state = get_all_state()
    for c in companies:
        s = state.get(c["id"], {})
        c["status"] = s.get("status", "not-contacted")
        c["notes"] = s.get("notes", "")
        c["last_contacted"] = s.get("last_contacted")
        c["updated_at"] = s.get("updated_at")
    return companies

@app.get("/api/state")
def get_state():
    """Lightweight state-only map: {id: {status, notes, last_contacted}}"""
    return get_all_state()

@app.patch("/api/companies/{company_id}")
def update_company(company_id: str, update: CompanyUpdate):
    conn = get_db()
    now = datetime.utcnow().isoformat()
    conn.execute("""
        INSERT INTO company_state (id, status, notes, last_contacted, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            status      = COALESCE(excluded.status, status),
            notes       = COALESCE(excluded.notes, notes),
            last_contacted = COALESCE(excluded.last_contacted, last_contacted),
            updated_at  = excluded.updated_at
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

@app.post("/api/outreach")
def log_outreach(entry: OutreachEntry):
    conn = get_db()
    conn.execute(
        "INSERT INTO outreach_log (company_id, action, body) VALUES (?, ?, ?)",
        (entry.company_id, entry.action, entry.body)
    )
    if entry.action in ("emailed", "linkedin", "called"):
        conn.execute("""
            INSERT INTO company_state (id, status, last_contacted, updated_at)
            VALUES (?, 'emailed', datetime('now'), datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                status = 'emailed',
                last_contacted = datetime('now'),
                updated_at = datetime('now')
        """, (entry.company_id,))
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
            "SELECT * FROM outreach_log ORDER BY created_at DESC LIMIT 200"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/stats")
def get_stats():
    companies = load_companies()
    state = get_all_state()
    eligible = [c for c in companies if not (c.get("ev") or {}).get("level") == "no"]
    def st(c): return state.get(c["id"], {}).get("status", "not-contacted")
    return {
        "total_eligible": len(eligible),
        "total_all": len(companies),
        "ineligible": len(companies) - len(eligible),
        "not_contacted": sum(1 for c in eligible if st(c) == "not-contacted"),
        "emailed": sum(1 for c in eligible if st(c) in ("emailed", "responded", "interested")),
        "interested": sum(1 for c in eligible if st(c) == "interested"),
        "passed": sum(1 for c in eligible if st(c) == "passed"),
    }

@app.get("/api/resumes/{filename}")
def get_resume(filename: str):
    path = RESUME_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(path)

@app.get("/api/health")
def health():
    return {"ok": True}

# ── STATIC + SPA FALLBACK ─────────────────────────────────────────────────────

app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")
