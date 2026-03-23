"""
Seed the pipeline DB from data/companies.json
Sets all companies to 'not-contacted' if not already in DB.
Safe to re-run — skips existing rows.

Usage:
    python3 tools/seed.py
    python3 tools/seed.py --reset   # wipe all state and reseed
"""
import sqlite3, json, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
DB = BASE / "pipeline.db"
COMPANIES = BASE / "data" / "companies.json"

def seed(reset=False):
    conn = sqlite3.connect(DB)
    if reset:
        conn.execute("DELETE FROM company_state")
        print("Wiped existing state.")

    with open(COMPANIES) as f:
        companies = json.load(f)

    inserted = 0
    for c in companies:
        try:
            conn.execute(
                "INSERT INTO company_state (id, status, notes) VALUES (?, 'not-contacted', '')",
                (c["id"],)
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass  # already exists, skip

    conn.commit()
    conn.close()
    print(f"Seeded {inserted} companies ({len(companies) - inserted} already existed).")

if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)
