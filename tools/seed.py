"""
Seed the pipeline DB — company data lives here, not in any file.

Usage:
    python3 tools/seed.py
    python3 tools/seed.py --reset   # wipe everything and reseed
"""
import sqlite3, sys
from pathlib import Path

DB = Path(__file__).parent.parent / "pipeline.db"

COMPANIES = [
    # ── TIER 1: PLACEMENT AGENCIES ───────────────────────────────────────────
    dict(id="globalmonday", name="Global Monday", type="J1 Placement Agency — USA HQ",
         tier=1, priority="high", contact="globalmonday.org/about-us",
         why="J1 PLACEMENT AGENCY — they find the host company AND handle sponsorship. Seattle placements confirmed. Paid positions, fast placement (<4 weeks).",
         why_vi="AGENCY TUYỂN DỤNG J1 — họ tìm công ty host VÀ xử lý bảo lãnh. Đã xác nhận vị trí tại Seattle. Vị trí có lương, đặt chỗ nhanh (<4 tuần).",
         pitch="Submit profile → they find host + arrange J1 simultaneously.",
         pitch_vi="Nộp hồ sơ → họ tìm host + sắp xếp J1 cùng lúc.",
         link="globalmonday.org",
         ev_level="confirmed",
         ev_what="Confirmed: Seattle marketing placements",
         ev_quote='"Global Monday works with companies providing paid J-1 Internship and Training positions across the United States in cities such as Seattle… business placements including marketing, finance, business development." Placement in under 4 weeks. 25 years experience, 50+ countries.',
         ev_source="https://www.globalmonday.org/about-us", ev_date="Mar 23 2026",
         resume="resume_en_preview.jpg"),

    dict(id="cicd-seattle", name="Intrax/CICD Seattle", type="J1 Sponsor — Seattle HQ since 1997",
         tier=1, priority="high", contact="intsupport@intraxinc.com / +1 (877) 429-6753",
         why="LOCAL Seattle-HQ J1 sponsor (est. 1997, part of Intrax since 2022). Can do site visits locally, help find Seattle host companies directly.",
         why_vi="Nhà tài trợ J1 TRỤ SỞ tại Seattle (est. 1997). Hỗ trợ tìm công ty host ở Seattle trực tiếp.",
         pitch="Local presence = cheap site visit ($250 flat). Best option if Thomas creates LLC as host.",
         pitch_vi="Hiện diện địa phương = thăm địa điểm rẻ ($250 cố định).",
         link="cicdgo.com",
         ev_level="confirmed",
         ev_what="Confirmed: DOS-designated, Seattle HQ",
         ev_quote='"CICD is headquartered in Seattle, WA and operates as a U.S. Department of State-designated J-1 Visa sponsor… Since 1997, CICD has provided thousands of participants with affordable J-1 visa programs."',
         ev_source="https://www.cicdgo.com/about-us", ev_date="Mar 23 2026",
         resume="resume_en_preview.jpg"),

    dict(id="bridgeaspire", name="Bridge Aspire", type="J1 Placement Agency — All-inclusive",
         tier=1, priority="high", contact="bridgeaspire.com/paid-internships-usa",
         why="All-inclusive J1 placement: DS-7002, DS-2019, insurance, host company search, 24/7 support. Interns earn $2,000–$4,500/month.",
         why_vi="Agency J1 trọn gói: DS-7002, DS-2019, bảo hiểm, tìm host, hỗ trợ 24/7. Thực tập sinh kiếm $2,000–$4,500/tháng.",
         pitch="Pay $3,500–$5,000 program fee → they handle everything. Recoup in 3–4 months.",
         pitch_vi="Trả phí $3,500–$5,000 → họ lo mọi thứ. Thu hồi trong 3–4 tháng.",
         link="bridgeaspire.com/paid-internships-usa/become-an-intern-or-trainee/",
         ev_level="confirmed",
         ev_what="Confirmed: all-inclusive J1, $2–4.5K/mo",
         ev_quote='"Bridge Aspire participants earn between $2,000 and $4,500 per month… all-inclusive services: eligibility verification, resume formatting, interview coordination, DS-7002, DS-2019, medical insurance, 24/7 support."',
         ev_source="https://www.bridgeaspire.com/paid-internships-usa/become-an-intern-or-trainee/", ev_date="Mar 23 2026",
         resume="resume_en_preview.jpg"),

    dict(id="internships-usa", name="Internships USA (EU)", type="J1 Placement Agency — Seattle confirmed",
         tier=1, priority="high", contact="internships-usa.eu/internships-and-traineeships-in-seattle/",
         why="Confirmed Seattle marketing internship placements. Handles J1 sponsorship and host company matching.",
         why_vi="Đã xác nhận vị trí marketing tại Seattle. Xử lý cả bảo lãnh J1 và tìm host.",
         pitch="Submit profile → matched to Seattle marketing role + J1 in one package.",
         pitch_vi="Nộp hồ sơ → ghép cặp vị trí marketing Seattle + J1 trong một gói.",
         link="internships-usa.eu/internships-and-traineeships-in-seattle/",
         ev_level="confirmed",
         ev_what="Confirmed: Seattle marketing placements page",
         ev_quote='"Paid internships and traineeships in Seattle, WA" — dedicated Seattle page confirms marketing track available.',
         ev_source="https://internships-usa.eu/internships-and-traineeships-in-seattle/", ev_date="Mar 23 2026",
         resume="resume_en_preview.jpg"),

    # ── TIER 1: DIRECT OUTREACH ───────────────────────────────────────────────
    dict(id="remitly", name="Remitly", type="Fintech — Seattle HQ",
         tier=1, priority="high", contact="hr@remitly.com / linkedin.com/company/remitly",
         why="Immigrant community mission = perfect match. Blog shows J1 familiarity. Strong marketing team, Seattle HQ.",
         why_vi="Sứ mệnh cộng đồng nhập cư = phù hợp hoàn hảo. Blog cho thấy quen thuộc với J1.",
         pitch="Vietnamese-American story, Southeast Asian market expertise, immigrant mission alignment.",
         pitch_vi="Câu chuyện Việt-Mỹ, chuyên môn thị trường Đông Nam Á.",
         link="remitly.com/careers",
         ev_level="contact", ev_what="No explicit J1 policy — contact HR",
         ev_quote='Remitly publishes J1 visa educational guides ("The Definitive Guide to the J-1 Visa") showing familiarity. No explicit policy on careers page. Self-arranged J1 worth asking directly.',
         ev_source="https://www.remitly.com/blog/immigration/the-us-j1-visa/", ev_date="Mar 23 2026",
         resume="Mynga_Remitly_preview.jpg"),

    dict(id="tiktok-sea", name="TikTok Seattle", type="Social Media — Seattle office",
         tier=1, priority="high", contact='careers.tiktok.com — search "marketing intern"',
         why="Asia-Pacific marketing, identity match, heavy international hiring. H-1B for FT — J1 self-arranged worth asking.",
         why_vi="Marketing châu Á-TBD, phù hợp bản sắc, tuyển dụng quốc tế mạnh.",
         pitch="Native TikTok creator, Vietnamese market fluency, 8K organic following.",
         pitch_vi="Creator TikTok bản xứ, thành thạo thị trường Việt Nam, 8K followers.",
         link="careers.tiktok.com",
         ev_level="contact", ev_what="No J1 intern policy — HR ask needed",
         ev_quote='"Expect candidates to have proper work authorization within the country they are applying." H-1B confirmed for FT (979 LCAs FY2025). No explicit J1 intern policy.',
         ev_source="https://lifeattiktok.com/earlycareers", ev_date="Mar 23 2026",
         resume="Mynga_TikTok_preview.jpg"),

    dict(id="copacino", name="Copacino+Fujikado", type="Boutique Ad Agency — Seattle 98101",
         tier=1, priority="high", contact="LetsChat@copacino.com / (206) 467-6610",
         why="Top Seattle indie agency, year-round 3-month rotating intern program. No explicit J1 restriction.",
         why_vi="Agency indie hàng đầu Seattle, chương trình thực tập luân phiên 3 tháng.",
         pitch="Award-winning international student (AIGC Gold Singapore 2024), editorial portfolio, bilingual copywriting.",
         pitch_vi="Sinh viên quốc tế đoạt giải (AIGC Gold Singapore 2024), copywriting song ngữ.",
         link="copacino.com/internships",
         ev_level="contact", ev_what="Intern program confirmed — J1 policy unknown",
         ev_quote="Year-round 3-month rotations confirmed. No J1/visa language found. Small = flexible. Self-arranged J1 means zero paperwork for them.",
         ev_source="https://www.copacino.com/internships", ev_date="Mar 23 2026",
         resume="Mynga_Copacino_preview.jpg"),

    dict(id="mckinstry", name="McKinstry", type="Engineering/Sustainability — Seattle HQ",
         tier=1, priority="high", contact="mckinstry.com/join-us/jobs (BLUE intern program)",
         why="B.L.U.E. intern program confirmed active. No explicit J1 restriction. Mid-size = flexibility.",
         why_vi="Chương trình B.L.U.E. intern đang hoạt động. Không có hạn chế J1. Công ty vừa = linh hoạt.",
         pitch="Marketing intern with data analytics and campaign execution background.",
         pitch_vi="Thực tập marketing với nền tảng phân tích dữ liệu và thực thi chiến dịch.",
         link="mckinstry.com/join-us/blue-internship-program/",
         ev_level="contact", ev_what="Intern program confirmed — J1 policy unknown",
         ev_quote="B.L.U.E. program confirmed. No visa/J1 mention. Only 1 H-1B LCA filed 2022–2024 — self-arranged J1 costs them nothing.",
         ev_source="https://www.mckinstry.com/join-us/blue-internship-program/", ev_date="Mar 23 2026",
         resume="Mynga_McKinstry_preview.jpg"),

    dict(id="holland", name="Holland America Line", type="Cruise/Travel — Seattle HQ",
         tier=1, priority="high", contact="careers.hollandamerica.com",
         why="Active internship program (Social Media, HR). APAC/Vietnam-route relevance. No J1 restriction found.",
         why_vi="Chương trình thực tập đang hoạt động. Tuyến APAC/Việt Nam liên quan.",
         pitch="Vietnamese native, Southeast Asian consumer behavior expertise, multilingual marketing for APAC routes.",
         pitch_vi="Người Việt Nam bản địa, chuyên gia thị trường ĐNA, marketing đa ngôn ngữ.",
         link="careers.hollandamerica.com",
         ev_level="contact", ev_what="Intern program confirmed — J1 policy unknown",
         ev_quote="UW Career Center posted HAL 2026 Summer Social Media internship (Nov 2025). No J1/visa language. APAC routes make Vietnamese candidate especially relevant.",
         ev_source="https://careers.uw.edu/blog/2025/11/07/holland-america-line-2026-internship-social-media-summer/", ev_date="Mar 23 2026",
         resume="Mynga_Holland_preview.jpg"),

    # ── TIER 2 ────────────────────────────────────────────────────────────────
    dict(id="tableau", name="Salesforce / Tableau", type="Tech — Seattle office",
         tier=2, priority="med", contact="careers.salesforce.com",
         why="CONFIRMED live Summer 2026 Global Paid Media marketing intern posting (job ID jr329802).",
         why_vi="Đã xác nhận vị trí thực tập marketing Hè 2026 đang mở.",
         pitch="Data analytics fluency, marketing automation, campaign measurement.",
         link="careers.salesforce.com",
         ev_level="contact", ev_what="Live 2026 role confirmed — J1 policy unknown",
         ev_quote='"Summer 2026 Intern — Global Field Marketing, Paid Media" confirmed at careers.salesforce.com (job ID jr329802). No explicit J1 policy.',
         ev_source="https://careers.salesforce.com/en/jobs/jr329802/summer-2026-intern-global-field-marketing-paid-media/", ev_date="Mar 23 2026",
         resume="Mynga_Salesforce_preview.jpg"),

    dict(id="expedia", name="Expedia Group", type="Travel Tech — Seattle HQ",
         tier=2, priority="med", contact="careers.expediagroup.com",
         why="International intern program globally. Glassdoor notes visa sponsorship comes up in interviews.",
         pitch="Travel-oriented Vietnamese marketing student with digital content and social media analytics.",
         link="careers.expediagroup.com",
         ev_level="contact", ev_what="International program — J1 policy unclear",
         ev_quote='Glassdoor interview review: "They should ask basic questions like — will the candidate need visa sponsorship before scheduling an interview." Live consideration but no confirmed J1 acceptance.',
         ev_source="https://www.glassdoor.com/Interview/Expedia-interview-questions", ev_date="Mar 23 2026",
         resume="Mynga_Expedia_preview.jpg"),

    dict(id="sap-sea", name="SAP Seattle", type="Enterprise Software — Seattle office",
         tier=2, priority="med", contact="jobs.sap.com",
         why="German multinational = international-friendly culture. J1 common in German multinationals.",
         pitch="Data-driven marketing with analytics background relevant to SAP ecosystem.",
         link="jobs.sap.com",
         ev_level="contact", ev_what="International company — verify J1 policy",
         ev_quote="German multinational with international hiring practices. No direct J1 evidence found. Self-arranged J1 worth raising.",
         ev_source="https://jobs.sap.com", ev_date="Mar 23 2026",
         resume="resume_en_preview.jpg"),

    dict(id="wunderman", name="VML / Wunderman Thompson", type="WPP Agency — Seattle office",
         tier=2, priority="med", contact="vml.com/careers",
         why="WPP global agency with structured intern programs. International candidates common.",
         pitch="Full-funnel campaign experience across SMS/MMS/email/push, print design portfolio.",
         link="vml.com/careers",
         ev_level="contact", ev_what="Global agency — verify J1 policy",
         ev_quote="WPP/Publicis agencies are global holding companies — J1 interns common in agency networks. Verify with Seattle office.",
         ev_source="https://vml.com/careers", ev_date="Mar 23 2026",
         resume="Mynga_Copacino_preview.jpg"),

    # ── TIER 2: INELIGIBLE ────────────────────────────────────────────────────
    dict(id="tmobile", name="T-Mobile", type="Telecom — Bellevue WA",
         tier=2, priority="med", contact="careers.t-mobile.com",
         why="EXPLICIT NO — do not contact for J1.",
         pitch="Would be ideal ($26–47/hr, mobile marketing org) but blanket no-visa policy.",
         link="careers.t-mobile.com",
         ev_level="no", ev_what="EXPLICIT NO — direct quote from careers page",
         ev_quote='"The employer does not sponsor work visas for internship positions, which also applies to individuals with F-1 student status who desire sponsorship after they complete their education." — T-Mobile careers page.',
         ev_source="https://careers.t-mobile.com/internship", ev_date="Mar 23 2026",
         resume="Mynga_TMobile_preview.jpg"),

    dict(id="nordstrom", name="Nordstrom", type="Retail/Fashion — Seattle HQ",
         tier=2, priority="med", contact="careers.nordstrom.com",
         why="EXPLICIT NO — do not contact for J1.",
         pitch="Perfect fit (fashion background, 8K following) but no-visa policy is unambiguous.",
         link="careers.nordstrom.com",
         ev_level="no", ev_what="EXPLICIT NO — direct quote from careers FAQ",
         ev_quote='"At this time, we are unable to sponsor visas or work authorizations for internship roles." — Nordstrom Careers FAQ.',
         ev_source="https://careers.nordstrom.com/careers", ev_date="Mar 23 2026",
         resume="Mynga_Nordstrom_preview.jpg"),

    # ── TIER 3 ────────────────────────────────────────────────────────────────
    dict(id="starbucks", name="Starbucks", type="F&B / Brand — Seattle HQ",
         tier=3, priority="med", contact="careers.starbucks.com",
         why="Seattle iconic brand, 10-week internship program. No visa policy found explicitly.",
         pitch="Vietnam is a major Starbucks market — native insight on APAC consumer behavior.",
         link="careers.starbucks.com",
         ev_level="contact", ev_what="Intern program confirmed — J1 policy unknown",
         ev_quote='"College students considered in their junior year (or third year for international students)" — eligibility, not sponsorship. No J1/visa language on internship pages.',
         ev_source="https://careers.starbucks.com/discover-opportunities/internships/", ev_date="Mar 23 2026",
         resume="Mynga_Starbucks_preview.jpg"),

    dict(id="amazon-mktg", name="Amazon Marketing", type="Tech — Seattle HQ",
         tier=3, priority="med", contact="amazon.jobs (search marketing intern)",
         why="10,000 interns from 45 countries/year. Massive marketing org, international hire history.",
         pitch="Ecommerce background (ran own vintage store), data-driven campaigns, bilingual.",
         link="amazon.jobs",
         ev_level="contact", ev_what="International intern history — verify policy",
         ev_quote='"Amazon hires approximately 10,000 interns annually from over 45 countries." No explicit J1 intern policy stated.',
         ev_source="https://amazon.jobs", ev_date="Mar 23 2026",
         resume="Mynga_Amazon_preview.jpg"),

    dict(id="zillow", name="Zillow", type="PropTech — Seattle HQ",
         tier=3, priority="med", contact="zillow.com/careers",
         why="Large Seattle tech, marketing team, structured intern program.",
         pitch="Data analytics, social media strategy, digital marketing execution.",
         link="zillow.com/careers",
         ev_level="contact", ev_what="No J1 evidence found — contact HR",
         ev_quote="No J1-specific evidence found. Structured intern program but no international/visa policy stated publicly.",
         ev_source="https://zillow.com/careers", ev_date="Mar 23 2026",
         resume="resume_en_preview.jpg"),

    dict(id="holland-2", name="Holland America — via Agency", type="Via Global Monday / Bridge Aspire",
         tier=3, priority="med", contact="globalmonday.org or bridgeaspire.com",
         why="Request HAL as target host through placement agency. Agencies have existing relationships.",
         pitch="Agency approaches HAL on Nga's behalf — removes need to navigate visa policy directly.",
         link="globalmonday.org",
         ev_level="contact", ev_what="Agency path — circumvents direct HR barrier",
         ev_quote="Agencies like Global Monday and Bridge Aspire approach hosts on behalf of applicants. HAL internship confirmed open via UW Career Center (Nov 2025).",
         ev_source="https://www.globalmonday.org/about-us", ev_date="Mar 23 2026",
         resume="Mynga_Holland_preview.jpg"),
]


def seed(reset=False):
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON")

    if reset:
        conn.execute("DELETE FROM outreach_log")
        conn.execute("DELETE FROM company_state")
        conn.execute("DELETE FROM companies")
        print("Wiped all tables.")

    inserted = skipped = 0
    for c in COMPANIES:
        try:
            conn.execute("""
                INSERT INTO companies
                    (id,name,type,tier,priority,contact,why,why_vi,pitch,pitch_vi,
                     link,ev_level,ev_what,ev_quote,ev_source,ev_date,resume)
                VALUES (:id,:name,:type,:tier,:priority,:contact,:why,:why_vi,:pitch,:pitch_vi,
                        :link,:ev_level,:ev_what,:ev_quote,:ev_source,:ev_date,:resume)
            """, {k: c.get(k) for k in
                  ("id","name","type","tier","priority","contact","why","why_vi",
                   "pitch","pitch_vi","link","ev_level","ev_what","ev_quote",
                   "ev_source","ev_date","resume")})
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    conn.close()
    print(f"Inserted {inserted}, skipped {skipped} (already in DB).")


if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)
