"""
Company J1 eligibility evaluator
Checks a company's careers page for J1/visa language and updates data/companies.json.

Usage:
    python3 tools/eval_company.py --id remitly
    python3 tools/eval_company.py --all        # re-eval all 'contact' level entries
    python3 tools/eval_company.py --add        # interactive: add a new company

Requires: playwright (pip install playwright && playwright install chromium)
"""
import json, sys, argparse
from pathlib import Path

BASE = Path(__file__).parent.parent
COMPANIES_PATH = BASE / "data" / "companies.json"

INDICATORS_YES = [
    "j-1", "j1", "j1 visa", "exchange visitor", "ds-2019", "ds-7002",
    "sevis", "cultural exchange", "intern visa", "visa sponsorship available",
    "we sponsor", "sponsorship provided",
]
INDICATORS_NO = [
    "does not sponsor", "unable to sponsor", "cannot sponsor",
    "no visa sponsorship", "not able to provide visa", "must be authorized",
    "work authorization required", "us work authorization",
]

def check_page_text(text: str) -> dict:
    text_lower = text.lower()
    hits_yes = [kw for kw in INDICATORS_YES if kw in text_lower]
    hits_no  = [kw for kw in INDICATORS_NO  if kw in text_lower]
    if hits_no:
        return {"verdict": "no", "signals": hits_no}
    if hits_yes:
        return {"verdict": "confirmed", "signals": hits_yes}
    return {"verdict": "contact", "signals": []}

def eval_company(company: dict) -> dict:
    """Scrape the company's careers page and update ev dict."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed — run: pip install playwright && playwright install chromium")
        return company

    url = company.get("ev", {}).get("source") or f"https://{company['link']}"
    print(f"  Checking: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = browser.new_page()
        try:
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            text = page.inner_text("body")
        except Exception as e:
            print(f"  Error loading page: {e}")
            text = ""
        browser.close()

    result = check_page_text(text)
    print(f"  Verdict: {result['verdict']} | Signals: {result['signals']}")

    # Update ev in company dict
    if "ev" not in company:
        company["ev"] = {}
    company["ev"]["level"] = result["verdict"]
    if result["signals"]:
        company["ev"]["signals"] = result["signals"]

    return company

def save(companies):
    with open(COMPANIES_PATH, "w") as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(companies)} companies to {COMPANIES_PATH}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", help="Company ID to evaluate")
    parser.add_argument("--all", action="store_true", help="Re-evaluate all 'contact' level companies")
    parser.add_argument("--add", action="store_true", help="Interactive: add a new company")
    args = parser.parse_args()

    with open(COMPANIES_PATH) as f:
        companies = json.load(f)

    if args.id:
        idx = next((i for i, c in enumerate(companies) if c["id"] == args.id), None)
        if idx is None:
            print(f"Company '{args.id}' not found")
            return
        companies[idx] = eval_company(companies[idx])
        save(companies)

    elif args.all:
        to_eval = [c for c in companies if (c.get("ev") or {}).get("level") == "contact"]
        print(f"Evaluating {len(to_eval)} companies with 'contact' status...")
        for i, company in enumerate(companies):
            if (company.get("ev") or {}).get("level") == "contact":
                print(f"\n[{i+1}/{len(companies)}] {company['name']}")
                companies[companies.index(company)] = eval_company(company)
        save(companies)

    elif args.add:
        print("=== Add new company ===")
        c = {
            "id": input("ID (slug, e.g. 'acme-corp'): ").strip(),
            "name": input("Name: ").strip(),
            "type": input("Type (e.g. 'Agency — Seattle WA'): ").strip(),
            "tier": int(input("Tier (1/2/3): ").strip()),
            "priority": input("Priority (high/med): ").strip(),
            "contact": input("Contact (email or URL): ").strip(),
            "why": input("Why target? ").strip(),
            "pitch": input("Pitch angle: ").strip(),
            "link": input("Careers URL (no https://): ").strip(),
            "ev": {
                "level": "contact",
                "what": "Not yet evaluated",
                "quote": "",
                "source": "",
                "date": ""
            },
            "resume": "resume_en_preview.jpg"
        }
        companies.append(c)
        save(companies)
        print(f"Added {c['name']}. Run --id {c['id']} to evaluate J1 eligibility.")

    else:
        parser.print_help()
        print("\nCurrent company count by ev.level:")
        from collections import Counter
        counts = Counter((c.get("ev") or {}).get("level", "unknown") for c in companies)
        for lvl, n in sorted(counts.items()):
            print(f"  {lvl}: {n}")

if __name__ == "__main__":
    main()
