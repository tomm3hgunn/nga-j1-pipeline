# Nga J1 Pipeline — Research Workflow

How to find, evaluate, and add companies to the pipeline.

---

## 1. Find candidates

Search these sources for Seattle-area companies with marketing internship programs:

**Job boards (live postings):**
```
site:greenhouse.io "marketing intern" "Seattle" 2026
site:lever.co "marketing intern" "Seattle"
site:ashbyhq.com "marketing" "intern" "Seattle"
careers.linkedin.com → Internship → Marketing → Seattle, WA → 2026
```

**Agency-specific searches:**
```
"j1 intern" "marketing" "Seattle" site:indeed.com
"paid internship" "Seattle" "marketing" site:glassdoor.com
"j1 placement" "Seattle" marketing
```

**Direct sources:**
- UW Handshake / Career Center job board — strong Seattle internship listings
- `myvisajobs.com` → company name → check H-1B LCA count (proxy for intl hiring culture)
- Placement agencies (Global Monday, Bridge Aspire, Internships USA) — ask directly what Seattle companies they currently place into

---

## 2. Evaluate J1 eligibility

For each company, check these signals in order:

### Hard NO signals (any = `ev_level: no`)
- "does not sponsor work visas for internship"
- "unable to sponsor visas or work authorizations for internship roles"
- "must be authorized to work in the US without sponsorship"
- "F-1 CPT/OPT only" with no J-1 mention

Check: careers page intern job postings, careers FAQ page, Glassdoor "interview" tab

### Hard YES signals (`ev_level: confirmed`)
- Explicit J-1 language on careers or internship page
- DOS-designated sponsor organization
- "exchange visitor program" mentioned
- Active DS-7002 / DS-2019 issuance history

### Soft YES (`ev_level: contact`)
- H-1B LCA filings > 5/year (company sponsors international workers, likely flexible)
- International intern program explicitly listed
- Glassdoor: visa sponsorship comes up in interview questions
- German/Japanese/multinational parent company (international hiring culture)
- Company publishes J-1 visa guides or immigration content (shows familiarity)

### Automated check:
```bash
python3 tools/eval_company.py --id <company-id>
# Scrapes their careers page and flags visa language automatically
```

---

## 3. Add a company

### Via CLI (interactive):
```bash
python3 tools/eval_company.py --add
# Prompts for: id, name, type, tier, contact, why, pitch, link
# Then auto-scrapes the careers page for J1 signals
```

### Via API (direct):
```bash
curl -X POST http://localhost:4005/api/companies \
  -H "Content-Type: application/json" \
  -d '{
    "id": "acme-corp",
    "name": "Acme Corp",
    "type": "Agency — Seattle WA",
    "tier": 2,
    "priority": "med",
    "contact": "careers@acme.com",
    "why": "Why this company is a good fit",
    "pitch": "Nga pitch angle for this company",
    "link": "acme.com/careers",
    "ev_level": "contact",
    "ev_what": "Initial finding — not yet verified",
    "ev_source": "https://acme.com/careers"
  }'
```

### Via dashboard:
Open the pipeline at `/nga-pipeline/` → click any company → Edit button (TBD)

---

## 4. Re-evaluate a company

```bash
# Re-scrape careers page for updated J1 language:
python3 tools/eval_company.py --id remitly

# Re-scrape all companies currently marked 'contact':
python3 tools/eval_company.py --all
```

---

## 5. Track outreach

When an email is sent, log it via API — this auto-sets status to `emailed`:
```bash
curl -X POST http://localhost:4005/api/outreach \
  -H "Content-Type: application/json" \
  -d '{"company_id": "remitly", "action": "emailed", "body": "Sent intro email to hr@remitly.com"}'
```

Actions: `emailed` | `called` | `linkedin` | `responded` | `met`

---

## 6. Priority tiers

| Tier | Criteria |
|------|----------|
| 1 | Confirmed J1 path OR placement agency (handles everything) |
| 2 | Strong target — active intern program, no hard NO found |
| 3 | Worth outreach — less certain fit or lower priority |

Ineligible (`ev_level: no`) = hidden from main view, excluded from counts.

---

## DB reset (if needed)

```bash
# Wipe company_state and outreach_log only (keep company list):
sqlite3 pipeline.db "DELETE FROM outreach_log; DELETE FROM company_state;"

# Full reset (wipe everything — re-add companies manually or via eval_company):
sqlite3 pipeline.db "DELETE FROM outreach_log; DELETE FROM company_state; DELETE FROM companies;"
```
