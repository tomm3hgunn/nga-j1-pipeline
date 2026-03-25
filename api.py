"""
Nga J1 Pipeline — FastAPI backend
Port: 4005

Tables:
  companies     — static company data (seeded once, editable via API)
  company_state — mutable outreach state (status, notes, last_contacted)
  outreach_log  — event log per company
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Optional

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "pipeline.db"
RESUME_DIR = Path("/workspace/group/candidates/mynga/resumes/output")

app = FastAPI(docs_url=None, redoc_url=None)

# Strip hub app-prefix so routes work whether called directly or via proxy
class StripPrefixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.scope["path"]
        for prefix in ("/nga-pipeline",):
            if path.startswith(prefix + "/") or path == prefix:
                request.scope["path"] = path[len(prefix):] or "/"
                request.scope["raw_path"] = request.scope["path"].encode()
        return await call_next(request)

app.add_middleware(StripPrefixMiddleware)

# ── DB ────────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS companies (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            type        TEXT,
            tier        INTEGER NOT NULL DEFAULT 2,
            priority    TEXT NOT NULL DEFAULT 'med',
            contact     TEXT,
            why         TEXT,
            why_vi      TEXT,
            pitch       TEXT,
            pitch_vi    TEXT,
            link        TEXT,
            ev_level    TEXT NOT NULL DEFAULT 'contact',
            ev_what     TEXT,
            ev_quote    TEXT,
            ev_source   TEXT,
            ev_date     TEXT,
            resume      TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS company_state (
            id              TEXT PRIMARY KEY REFERENCES companies(id),
            status          TEXT NOT NULL DEFAULT 'not-contacted',
            notes           TEXT NOT NULL DEFAULT '',
            last_contacted  TEXT,
            updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS outreach_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id  TEXT NOT NULL REFERENCES companies(id),
            action      TEXT NOT NULL,
            body        TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

init_db()

# ── MODELS ────────────────────────────────────────────────────────────────────

class CompanyUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    last_contacted: Optional[str] = None

class CompanyCreate(BaseModel):
    id: str
    name: str
    type: Optional[str] = None
    tier: int = 2
    priority: str = "med"
    contact: Optional[str] = None
    why: Optional[str] = None
    why_vi: Optional[str] = None
    pitch: Optional[str] = None
    pitch_vi: Optional[str] = None
    link: Optional[str] = None
    ev_level: str = "contact"
    ev_what: Optional[str] = None
    ev_quote: Optional[str] = None
    ev_source: Optional[str] = None
    ev_date: Optional[str] = None
    resume: Optional[str] = None

class OutreachEntry(BaseModel):
    company_id: str
    action: str  # emailed | called | linkedin | responded | met
    body: Optional[str] = None

# ── HELPERS ───────────────────────────────────────────────────────────────────

def row_to_company(row) -> dict:
    d = dict(row)
    # Reconstruct nested ev object for frontend compat
    d["ev"] = {
        "level":  d.pop("ev_level", "contact"),
        "what":   d.pop("ev_what", ""),
        "quote":  d.pop("ev_quote", ""),
        "source": d.pop("ev_source", ""),
        "date":   d.pop("ev_date", ""),
    }
    return d

# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/api/companies")
def get_companies(tier: Optional[int] = None, ev_level: Optional[str] = None):
    """All companies merged with their live state."""
    conn = get_db()
    clauses, params = [], []
    if tier:
        clauses.append("c.tier = ?"); params.append(tier)
    if ev_level:
        clauses.append("c.ev_level = ?"); params.append(ev_level)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = conn.execute(f"""
        SELECT c.*,
               COALESCE(s.status, 'not-contacted') AS status,
               COALESCE(s.notes, '')               AS notes,
               s.last_contacted,
               s.updated_at
        FROM companies c
        LEFT JOIN company_state s ON s.id = c.id
        {where}
        ORDER BY c.tier, c.priority DESC, c.name
    """, params).fetchall()
    conn.close()
    return [row_to_company(r) for r in rows]

@app.get("/api/companies/{company_id}")
def get_company(company_id: str):
    conn = get_db()
    row = conn.execute("""
        SELECT c.*,
               COALESCE(s.status, 'not-contacted') AS status,
               COALESCE(s.notes, '')               AS notes,
               s.last_contacted, s.updated_at
        FROM companies c
        LEFT JOIN company_state s ON s.id = c.id
        WHERE c.id = ?
    """, (company_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    return row_to_company(row)

@app.post("/api/companies")
def add_company(c: CompanyCreate):
    conn = get_db()
    conn.execute("""
        INSERT INTO companies
            (id,name,type,tier,priority,contact,why,why_vi,pitch,pitch_vi,
             link,ev_level,ev_what,ev_quote,ev_source,ev_date,resume)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (c.id,c.name,c.type,c.tier,c.priority,c.contact,c.why,c.why_vi,
          c.pitch,c.pitch_vi,c.link,c.ev_level,c.ev_what,c.ev_quote,
          c.ev_source,c.ev_date,c.resume))
    conn.commit()
    conn.close()
    return get_company(c.id)

@app.patch("/api/companies/{company_id}")
def update_state(company_id: str, update: CompanyUpdate):
    conn = get_db()
    now = datetime.utcnow().isoformat()
    conn.execute("""
        INSERT INTO company_state (id, status, notes, last_contacted, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            status         = COALESCE(excluded.status, status),
            notes          = COALESCE(excluded.notes, notes),
            last_contacted = COALESCE(excluded.last_contacted, last_contacted),
            updated_at     = excluded.updated_at
    """, (company_id, update.status or "not-contacted",
          update.notes or "", update.last_contacted, now))
    conn.commit()
    conn.close()
    return get_company(company_id)

@app.post("/api/outreach")
def log_outreach(entry: OutreachEntry):
    conn = get_db()
    conn.execute(
        "INSERT INTO outreach_log (company_id, action, body) VALUES (?,?,?)",
        (entry.company_id, entry.action, entry.body)
    )
    if entry.action in ("emailed", "linkedin", "called"):
        conn.execute("""
            INSERT INTO company_state (id, status, last_contacted, updated_at)
            VALUES (?, 'emailed', datetime('now'), datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                status = 'emailed', last_contacted = datetime('now'),
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
            (company_id,)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM outreach_log ORDER BY created_at DESC LIMIT 200"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/stats")
def get_stats():
    conn = get_db()
    rows = conn.execute("""
        SELECT c.ev_level,
               COALESCE(s.status,'not-contacted') AS status
        FROM companies c
        LEFT JOIN company_state s ON s.id = c.id
    """).fetchall()
    conn.close()
    eligible = [r for r in rows if r["ev_level"] != "no"]
    def cnt(rows, st): return sum(1 for r in rows if r["status"] == st)
    return {
        "total_eligible": len(eligible),
        "total_all": len(rows),
        "ineligible": len(rows) - len(eligible),
        "not_contacted": cnt(eligible, "not-contacted"),
        "emailed": sum(1 for r in eligible if r["status"] in ("emailed","responded","interested")),
        "interested": cnt(eligible, "interested"),
        "passed": cnt(eligible, "passed"),
    }

@app.get("/api/resumes/{filename}")
def get_resume(filename: str):
    path = RESUME_DIR / Path(filename).name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(path)

@app.get("/api/health")
def health():
    return {"ok": True}

# ── STATIC (must be last) ─────────────────────────────────────────────────────

app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")
