"""
Seed the pipeline DB from data/companies.json → companies table.
Safe to re-run — skips existing rows unless --reset.

Usage:
    python3 tools/seed.py
    python3 tools/seed.py --reset   # wipe companies + state and reseed
"""
import sqlite3, json, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
DB   = BASE / "pipeline.db"
SRC  = BASE / "data" / "companies.json"

def seed(reset=False):
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON")

    if reset:
        conn.execute("DELETE FROM outreach_log")
        conn.execute("DELETE FROM company_state")
        conn.execute("DELETE FROM companies")
        print("Wiped all tables.")

    with open(SRC) as f:
        companies = json.load(f)

    inserted = skipped = 0
    for c in companies:
        ev = c.get("ev") or {}
        try:
            conn.execute("""
                INSERT INTO companies
                    (id,name,type,tier,priority,contact,why,why_vi,pitch,pitch_vi,
                     link,ev_level,ev_what,ev_quote,ev_source,ev_date,resume)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                c["id"], c["name"], c.get("type"), c.get("tier",2),
                c.get("priority","med"), c.get("contact"),
                c.get("why"), c.get("why_vi"), c.get("pitch"), c.get("pitch_vi"),
                c.get("link"),
                ev.get("level","contact"), ev.get("what"), ev.get("quote"),
                ev.get("source"), ev.get("date"),
                c.get("resume"),
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    conn.close()
    print(f"Inserted {inserted} companies, skipped {skipped} (already in DB).")

if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)
