"""
Company J1 eligibility evaluator — adds and re-evaluates companies in the DB.

Usage:
    python3 tools/eval_company.py --add              # interactive: add a new company
    python3 tools/eval_company.py --id remitly       # re-scrape one company
    python3 tools/eval_company.py --all              # re-scrape all 'contact' companies
    python3 tools/eval_company.py                    # show counts by ev_level

Requires: playwright (pip install playwright && playwright install chromium)
"""
import sqlite3, sys, argparse
from pathlib import Path
from datetime import datetime

DB = Path(__file__).parent.parent / "pipeline.db"

SIGNALS_NO = [
    "does not sponsor work visas for internship",
    "unable to sponsor visas",
    "cannot sponsor",
    "no visa sponsorship",
    "not able to provide visa",
    "must be authorized to work",
    "work authorization required",
    "f-1 cpt/opt only",
]
SIGNALS_YES = [
    "j-1", "j1 visa", "j1 intern", "exchange visitor",
    "ds-2019", "ds-7002", "sevis",
    "cultural exchange", "visa sponsorship available", "we sponsor",
]

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def scrape_page(url: str) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed — run: pip install playwright && playwright install chromium")
        return ""
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = browser.new_page()
        try:
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            text = page.inner_text("body")
        except Exception as e:
            print(f"  Error: {e}")
            text = ""
        browser.close()
    return text

def evaluate_text(text: str) -> dict:
    low = text.lower()
    hits_no  = [s for s in SIGNALS_NO  if s in low]
    hits_yes = [s for s in SIGNALS_YES if s in low]
    if hits_no:
        return {"level": "no",        "signals": hits_no}
    if hits_yes:
        return {"level": "confirmed", "signals": hits_yes}
    return {"level": "contact",   "signals": []}

def update_ev(company_id: str, result: dict, source_url: str):
    conn = get_db()
    conn.execute("""
        UPDATE companies SET
            ev_level = ?,
            ev_what  = ?,
            ev_date  = ?
        WHERE id = ?
    """, (result["level"],
          f"Auto-detected signals: {', '.join(result['signals']) or 'none'}",
          datetime.utcnow().strftime("%-d %b %Y"),
          company_id))
    conn.commit()
    conn.close()

def show_counts():
    conn = get_db()
    rows = conn.execute(
        "SELECT ev_level, COUNT(*) n FROM companies GROUP BY ev_level"
    ).fetchall()
    conn.close()
    total = sum(r["n"] for r in rows)
    print(f"Companies in DB: {total}")
    for r in rows:
        print(f"  {r['ev_level']:12} {r['n']}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id",  help="Re-evaluate one company by ID")
    parser.add_argument("--all", action="store_true", help="Re-evaluate all 'contact' companies")
    parser.add_argument("--add", action="store_true", help="Interactive: add a new company")
    args = parser.parse_args()

    if args.id:
        conn = get_db()
        row = conn.execute("SELECT * FROM companies WHERE id=?", (args.id,)).fetchone()
        conn.close()
        if not row:
            print(f"Company '{args.id}' not found in DB")
            return
        url = row["ev_source"] or f"https://{row['link']}"
        print(f"Scraping: {url}")
        text = scrape_page(url)
        result = evaluate_text(text)
        print(f"Verdict: {result['level']} | Signals: {result['signals']}")
        update_ev(args.id, result, url)
        print("Updated.")

    elif args.all:
        conn = get_db()
        rows = conn.execute(
            "SELECT id, name, ev_source, link FROM companies WHERE ev_level='contact'"
        ).fetchall()
        conn.close()
        print(f"Re-evaluating {len(rows)} companies...")
        for r in rows:
            url = r["ev_source"] or f"https://{r['link']}"
            print(f"\n{r['name']} — {url}")
            text = scrape_page(url)
            result = evaluate_text(text)
            print(f"  {result['level']} | {result['signals']}")
            update_ev(r["id"], result, url)
        print("\nDone.")

    elif args.add:
        print("=== Add company to DB ===")
        fields = {
            "id":       input("ID (slug, e.g. acme-corp): ").strip(),
            "name":     input("Name: ").strip(),
            "type":     input("Type (e.g. Agency — Seattle WA): ").strip(),
            "tier":     int(input("Tier (1/2/3): ").strip()),
            "priority": input("Priority (high/med): ").strip() or "med",
            "contact":  input("Contact (email or URL): ").strip(),
            "why":      input("Why target? ").strip(),
            "pitch":    input("Pitch angle: ").strip(),
            "link":     input("Careers URL (no https://): ").strip(),
            "ev_source":input("Evidence URL to scrape: ").strip(),
        }
        # Auto-scrape
        if fields["ev_source"]:
            print(f"Scraping {fields['ev_source']}...")
            text = scrape_page(fields["ev_source"])
            result = evaluate_text(text)
            print(f"Verdict: {result['level']} | Signals: {result['signals']}")
        else:
            result = {"level": "contact", "signals": []}

        conn = get_db()
        conn.execute("""
            INSERT INTO companies
                (id,name,type,tier,priority,contact,why,pitch,link,
                 ev_level,ev_what,ev_source,ev_date,resume)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (fields["id"], fields["name"], fields["type"], fields["tier"],
              fields["priority"], fields["contact"], fields["why"],
              fields["pitch"], fields["link"],
              result["level"],
              f"Auto-detected: {', '.join(result['signals']) or 'not yet evaluated'}",
              fields["ev_source"],
              datetime.utcnow().strftime("%-d %b %Y"),
              "resume_en_preview.jpg"))
        conn.commit()
        conn.close()
        print(f"Added {fields['name']} (ev_level: {result['level']})")

    else:
        show_counts()

if __name__ == "__main__":
    main()
