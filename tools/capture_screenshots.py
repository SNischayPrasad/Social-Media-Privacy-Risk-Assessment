"""
Capture the portfolio screenshots listed in screenshots/README.md.

    pip install -r requirements-dev.txt
    python tools/capture_screenshots.py              # screenshots 01-26
    python tools/capture_screenshots.py --github     # also 27-29 from the public GitHub repo

How it works
    * Starts its own copy of the app on a random localhost port with a TEMPORARY
      database, so your real database is never touched.
    * Drives your installed Google Chrome with Playwright (no browser download).
    * Uses only the fictional demo profile - no real personal data appears.
    * Terminal / dataset / schema images are rendered from REAL command output
      and real files (pytest output, the CSV, the SQLite schema).
"""

import argparse
import base64
import csv
import html
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from playwright.sync_api import sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from backend.app import create_app  # noqa: E402
from backend.config import Config  # noqa: E402
from backend.models.database import Database  # noqa: E402

OUT = os.path.join(PROJECT_ROOT, "screenshots")
REPO_URL = "https://github.com/SNischayPrasad/Social-Media-Privacy-Risk-Assessment"
SCALE = 1.5

# The 11 improvements from the brief's demonstration (section 32).
DEMO_FIXES = ["phone_public", "birthday_public", "location_public", "realtime_location_sharing",
              "travel_posts", "unknown_connections", "verify_unknown_profiles", "tag_review_enabled",
              "mfa_enabled", "login_alerts_enabled", "third_party_apps_reviewed"]

FONT_LINK = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@'
             '62..125,400..900&family=IBM+Plex+Mono:wght@400;500;600&family=Public+Sans:wght@400;500;600;700'
             '&display=swap">')

BASE_CSS = """
*{box-sizing:border-box} body{margin:0;background:#f3f5f8;font-family:'Public Sans',system-ui,sans-serif;color:#12151c}
.frame{margin:28px;border-radius:12px;overflow:hidden;box-shadow:0 10px 30px -12px rgba(0,0,0,.35);background:#fff;border:1px solid #dce1e9}
.bar{display:flex;align-items:center;gap:8px;padding:10px 14px;background:#e9edf2;border-bottom:1px solid #dce1e9;font:500 13px 'IBM Plex Mono',monospace;color:#4a5160}
.bar i{width:12px;height:12px;border-radius:50%;display:inline-block}.bar i:nth-child(1){background:#ff5f57}.bar i:nth-child(2){background:#febc2e}.bar i:nth-child(3){background:#28c840}
.bar span{margin-left:8px}
.term{background:#11141a;color:#d8dde6;font:14px/1.55 'IBM Plex Mono',Consolas,monospace;padding:18px 22px;white-space:pre}
.term .ok{color:#3ecf5b}.term .dim{color:#7c8494}.term .hl{color:#ffe14d}.term .bad{color:#ff6b6b}
h1{font:800 26px 'Archivo',sans-serif;font-stretch:125%;margin:0 0 6px}
.sub{color:#4a5160;margin:0 0 18px;font-size:15px}
.pad{padding:26px 30px}
"""


def page_html(body, extra_css=""):
    return (f"<!doctype html><html><head><meta charset='utf-8'>{FONT_LINK}"
            f"<style>{BASE_CSS}{extra_css}</style></head><body>{body}</body></html>")


# ------------------------------------------------------------------ helpers
def save(page, name, full_page=False):
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=full_page)
    print("  saved", name)


def region(page, name, selectors, pad=20, max_height=None):
    """Screenshot the union of the given elements, with padding."""
    # The sticky header would overlap cropped regions in a full-page capture.
    page.evaluate("() => { const h = document.querySelector('.site-header'); if (h) h.style.position = 'static'; }")
    boxes = []
    for sel in selectors:
        loc = page.locator(sel).first
        loc.scroll_into_view_if_needed()
        box = loc.bounding_box()
        scroll_y = page.evaluate("window.scrollY")
        boxes.append((box["x"], box["y"] + scroll_y, box["x"] + box["width"], box["y"] + box["height"] + scroll_y))
    x0 = max(min(b[0] for b in boxes) - pad, 0)
    y0 = max(min(b[1] for b in boxes) - pad, 0)
    x1 = max(b[2] for b in boxes) + pad
    y1 = max(b[3] for b in boxes) + pad
    if max_height:
        y1 = min(y1, y0 + max_height)
    page.screenshot(path=os.path.join(OUT, name), full_page=True,
                    clip={"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0})
    print("  saved", name)


def card_of(selector):
    return f"{selector} >> xpath=ancestor-or-self::*[contains(concat(' ',normalize-space(@class),' '),' card ')][1]"


def settle(page):
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready.then(() => true)")
    page.wait_for_timeout(300)


def render(browser, name, markup, width=1200, full_page=True):
    page = browser.new_page(viewport={"width": width, "height": 700}, device_scale_factor=SCALE)
    page.set_content(markup, wait_until="networkidle")
    page.evaluate("document.fonts.ready.then(() => true)")
    save(page, name, full_page=full_page)
    page.close()


# ------------------------------------------------------------------ rendered (non-app) images
def project_tree():
    skip = {"venv", "__pycache__", "instance", ".pytest_cache", ".git", "screenshots"}
    lines = ["Social-Media-Privacy-Risk-Assessment/"]

    def walk(folder, prefix):
        entries = sorted(e for e in os.listdir(folder) if e not in skip and not e.endswith(".pyc"))
        entries.sort(key=lambda e: (not os.path.isdir(os.path.join(folder, e)), e.lower()))
        for i, entry in enumerate(entries):
            last = i == len(entries) - 1
            full = os.path.join(folder, entry)
            lines.append(f"{prefix}{'└── ' if last else '├── '}{entry}{'/' if os.path.isdir(full) else ''}")
            if os.path.isdir(full):
                walk(full, prefix + ("    " if last else "│   "))

    walk(PROJECT_ROOT, "")
    lines.append("screenshots/   (this folder)")
    return "\n".join(lines)


def architecture_html():
    css = """
    .wrap{padding:34px 40px;background:#fff}
    .row{display:flex;justify-content:center;margin:0}
    .box{border:1.5px solid #12151c;border-radius:8px;padding:10px 18px;font-weight:600;background:#fff;text-align:center;min-width:300px}
    .box small{display:block;font:500 12px 'IBM Plex Mono',monospace;color:#737b8b;font-weight:500}
    .arrow{text-align:center;color:#737b8b;font-size:20px;line-height:26px}
    .grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;border:1.5px dashed #2440c9;border-radius:10px;padding:12px;background:#e5e9fb;max-width:1040px;margin:0 auto}
    .grid div{background:#fff;border:1px solid #dce1e9;border-radius:6px;padding:8px;font-size:13px;font-weight:600;text-align:center}
    .grid div b{display:block;font:500 11px 'IBM Plex Mono',monospace;color:#737b8b}
    .mark{background:linear-gradient(transparent 12%,#ffe14d 12%,#ffe14d 88%,transparent 88%);padding:0 4px}
    .side{max-width:1040px;margin:22px auto 0;display:flex;gap:14px}
    .side .box{flex:1;min-width:0}
    .opt{border-style:dashed}
    """
    cats = ["A Profile", "B Personal Info", "C Location", "D Content", "E Connections",
            "F Tagging", "G Account Security", "H Third-Party Apps", "I Social Engineering", "J Digital Footprint"]
    grid = "".join(f"<div><b>{c.split(' ', 1)[0]}</b>{c.split(' ', 1)[1]}</div>" for c in cats)

    def box(title, sub):
        return f"<div class='row'><div class='box'>{title}<small>{sub}</small></div></div><div class='arrow'>↓</div>"

    body = f"""<div class='frame'><div class='wrap'>
    <h1>System architecture</h1><p class='sub'>Social Media Privacy Risk Assessment Framework · <span class='mark'>no raw answers are ever stored</span></p>
    {box('User', 'browser · answers kept in this tab only')}
    {box('Privacy Questionnaire', '53 questions · fixed answer codes')}
    {box('Input Validation', 'allow-list of question ids and answers')}
    {box('Feature Extraction', 'each answer → risk value 0.0–1.0')}
    <div class='grid'>{grid}</div><div class='arrow'>↓</div>
    {box('Category Scores → Risk Scoring Engine', 'weighted average · configurable weights')}
    {box('Overall Risk + Classification', 'LOW 0–20 · MODERATE 21–40 · HIGH 41–70 · CRITICAL 71–100')}
    {box('Findings Engine → Recommendation Engine', 'ranked findings · Immediate / Important / Good practice')}
    <div class='side'>
      <div class='box'>Privacy Dashboard<small>6 charts · synthetic comparison</small></div>
      <div class='box'>Improvement Simulator<small>what-if · nothing stored</small></div>
      <div class='box'>Privacy Report<small>HTML → PDF · no personal data</small></div>
      <div class='box opt'>Analytics DB (opt-in)<small>scores + finding types only</small></div>
    </div></div></div>"""
    return page_html(body, css)


def terminal_html(title, command, output):
    colored = []
    for line in output.splitlines():
        esc = html.escape(line)
        if "PASSED" in line:
            esc = esc.replace("PASSED", "<span class='ok'>PASSED</span>")
        if "FAILED" in line:
            esc = esc.replace("FAILED", "<span class='bad'>FAILED</span>")
        if " passed" in line and "=" in line:
            esc = f"<span class='ok'>{esc}</span>"
        colored.append(esc)
    body = (f"<div class='frame'><div class='bar'><i></i><i></i><i></i><span>{html.escape(title)}</span></div>"
            f"<div class='term'><span class='hl'>PS&gt;</span> {html.escape(command)}\n{chr(10).join(colored)}</div></div>")
    return page_html(body)


def run_pytest(args):
    result = subprocess.run([sys.executable, "-m", "pytest", *args, "-p", "no:cacheprovider"],
                            cwd=PROJECT_ROOT, capture_output=True, text=True)
    lines = [ln.replace(PROJECT_ROOT, "C:\\...\\Social-Media-Privacy-Risk-Assessment")
             for ln in result.stdout.splitlines()
             if not ln.startswith(("cachedir", "rootdir", "plugins"))]
    return "\n".join(lines).strip()


def dataset_html():
    path = os.path.join(PROJECT_ROOT, "data", "social_media_privacy_assessments.csv")
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    cols = ["profile_id", "synthetic_persona", "profile_visibility", "phone_public", "birthday_public",
            "location_public", "travel_posts", "unknown_connections", "mfa_enabled", "tag_review_enabled",
            "password_reuse_reported", "risk_score", "risk_level"]
    colours = {"LOW": "#0ca30c", "MODERATE": "#fab219", "HIGH": "#ec835a", "CRITICAL": "#d03b3b"}
    head = "".join(f"<th>{c}</th>" for c in cols)
    body_rows = ""
    for r in rows[:18]:
        cells = ""
        for c in cols:
            v = html.escape(r[c])
            if c == "risk_level":
                v = f"<span class='dot' style='background:{colours[r[c]]}'></span>{v}"
            cells += f"<td>{v}</td>"
        body_rows += f"<tr>{cells}</tr>"
    total = len(rows)
    counts = {lvl: sum(1 for r in rows if r['risk_level'] == lvl) for lvl in colours}
    summary = " · ".join(f"{k} {v}" for k, v in counts.items())
    css = """
    table{border-collapse:collapse;font:12.5px 'IBM Plex Mono',monospace;width:100%}
    th{background:#eceff4;text-align:left;padding:7px 8px;border:1px solid #dce1e9;font-weight:600;white-space:nowrap}
    td{padding:6px 8px;border:1px solid #e6e9ef;white-space:nowrap}
    tr:nth-child(even) td{background:#fafbfc}
    .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
    """
    body = (f"<div class='frame'><div class='bar'><i></i><i></i><i></i><span>data/social_media_privacy_assessments.csv"
            f"</span></div><div class='pad'><h1>Synthetic privacy-assessment dataset</h1>"
            f"<p class='sub'>{total:,} fictional records · {len(rows[0])} columns ({len(cols)} shown) · scored by the app's own engine · "
            f"{summary}</p><table><tr>{head}</tr>{body_rows}</table>"
            f"<p class='sub' style='margin-top:12px'>Showing rows 1–18 of {total:,}. No names, contact details "
            f"or real people: IDs are SYN-xxxxx.</p></div></div>")
    return page_html(body, css)


def schema_html():
    tmp = tempfile.mkdtemp()
    db = Database(os.path.join(tmp, "schema.db"))
    db.init_schema()
    with sqlite3.connect(db.path) as conn:
        sql = [r[0] for r in conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    columns = db.table_columns()
    cards = ""
    for table in ("assessments", "category_scores", "findings", "recommendations"):
        cols = "".join(f"<li>{html.escape(c)}</li>" for c in columns[table])
        cards += f"<div class='tbl'><h3>{table.upper()}</h3><ul>{cols}</ul></div>"
    never = ["phone numbers", "email addresses", "home addresses", "birth dates", "passwords",
             "exact locations", "private messages", "questionnaire answers", "IP addresses"]
    never_html = "".join(f"<span>{n}</span>" for n in never)
    css = """
    .tbls{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}
    .tbl{border:1.5px solid #12151c;border-radius:8px;overflow:hidden}
    .tbl h3{margin:0;padding:8px 12px;background:#12151c;color:#fff;font:600 14px 'IBM Plex Mono',monospace}
    .tbl ul{list-style:none;margin:0;padding:8px 12px;font:13px/1.8 'IBM Plex Mono',monospace}
    .rel{font:13px 'IBM Plex Mono',monospace;color:#4a5160;margin:0 0 16px}
    .term{font-size:12.5px;border-radius:8px}
    .never{margin-top:16px;display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:14px}
    .never span{background:#12151c;color:#fff;padding:3px 10px;border-radius:3px;font:500 12px 'IBM Plex Mono',monospace}
    """
    body = (f"<div class='frame'><div class='pad'><h1>Privacy-first database schema (SQLite)</h1>"
            f"<p class='sub'>Only scores and finding types are stored, and only if the user opts in.</p>"
            f"<div class='tbls'>{cards}</div>"
            f"<p class='rel'>ASSESSMENTS 1 ──&lt; CATEGORY_SCORES &nbsp;·&nbsp; ASSESSMENTS 1 ──&lt; FINDINGS &gt;── "
            f"finding_type ── RECOMMENDATIONS &nbsp;·&nbsp; ON DELETE CASCADE</p>"
            f"<div class='term'>{html.escape(chr(10).join(s + ';' for s in sql))}</div>"
            f"<div class='never'><strong>Never stored:</strong>{never_html}</div></div></div>")
    return page_html(body, css)


# ------------------------------------------------------------------ app screenshots
def capture_app(browser, base):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=SCALE,
                              color_scheme="light", reduced_motion="reduce")
    page = ctx.new_page()

    page.goto(base + "/")
    settle(page)
    save(page, "03_homepage.png")

    page.goto(base + "/assessment.html")
    settle(page)
    page.wait_for_selector(".question")
    save(page, "04_questionnaire.png")

    page.click("#demo-btn")
    page.wait_for_timeout(500)
    for index, name in [(0, "05_profile_privacy_section.png"), (1, "06_personal_information_section.png"),
                        (2, "07_location_section.png"), (6, "08_account_security_section.png"),
                        (8, "09_social_engineering_section.png")]:
        page.locator("#steps button").nth(index).click()
        page.wait_for_timeout(250)
        region(page, name, [".assess-layout"], pad=16, max_height=1500)

    page.locator("#steps button").nth(9).click()
    page.click("#submit-btn")
    page.wait_for_selector("#results:not([hidden])")
    settle(page)
    region(page, "10_overall_risk_score.png", ["#results .page-head", "#stats"], pad=24)
    page.evaluate("document.querySelector('#category-chart').closest('.card').querySelector('details').open = true")
    region(page, "11_category_scores.png", [card_of("#category-chart")])
    page.evaluate("document.querySelector('#category-chart').closest('.card').querySelector('details').open = false")
    region(page, "12_privacy_risk_chart.png", [card_of("#category-chart")])
    region(page, "13_top_findings.png", [card_of("#top-findings"), card_of("#controls-table")])
    region(page, "14_recommendations.png", [card_of("#recommendations")], max_height=1400)

    page.click("#sim-none")
    for fix in DEMO_FIXES:
        page.check(f"#sim-options input[value='{fix}']")
    page.locator("#sim-options").evaluate("el => el.scrollTop = 0")
    region(page, "15_simulator_before.png", ["#simulator"])
    page.click("#sim-run")
    page.wait_for_selector("#sim-chart-wrap:not([hidden])")
    page.wait_for_timeout(500)
    region(page, "16_simulator_after.png", ["#simulator"])
    region(page, "17_risk_reduction.png", ["#sim-result", "#sim-chart-wrap"])

    page.goto(base + "/dashboard.html")
    settle(page)
    page.wait_for_timeout(500)
    save(page, "18_privacy_dashboard.png")
    region(page, "19_risk_distribution.png", [card_of("#chart-distribution"), card_of("#chart-controls")])
    region(page, "20_top_weaknesses_chart.png", [card_of("#chart-weaknesses"), card_of("#chart-footprint")])

    page.goto(base + "/checklist.html")
    settle(page)
    page.locator("#checklist input").nth(8).check()   # "Enable MFA" ticked for the demo
    save(page, "21_privacy_checklist.png", full_page=True)

    ctx.close()

    rpage = browser.new_page(viewport={"width": 1100, "height": 1500}, device_scale_factor=SCALE)
    rpage.goto("file:///" + os.path.join(PROJECT_ROOT, "reports", "demo_privacy_report.html").replace("\\", "/"))
    rpage.wait_for_timeout(300)
    save(rpage, "22_privacy_report.png")
    rpage.close()


def capture_github(browser):
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=SCALE, color_scheme="light")
    page.goto(REPO_URL + "/commits/main")
    page.wait_for_load_state("networkidle")
    save(page, "27_github_commits.png")
    page.goto(REPO_URL)
    page.wait_for_load_state("networkidle")
    save(page, "28_github_repository.png")
    readme = page.locator("article.markdown-body").first
    readme.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    region(page, "29_readme_preview.png", ["article.markdown-body"], pad=10, max_height=1500)
    page.close()


def main():
    parser = argparse.ArgumentParser(description="Capture portfolio screenshots.")
    parser.add_argument("--github", action="store_true", help="also capture 27-29 from the public GitHub repo")
    parser.add_argument("--github-only", action="store_true", help="capture only 27-29")
    args = parser.parse_args()
    os.makedirs(OUT, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        if not args.github_only:
            tmp_db = os.path.join(tempfile.mkdtemp(), "screenshots.db")
            app = create_app(Config, overrides={"DATABASE_PATH": tmp_db, "RATE_LIMIT_PER_MINUTE": 0})
            server = make_server("127.0.0.1", 0, app)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{server.server_port}"
            print("App running at", base)

            render(browser, "01_project_structure.png", terminal_html(
                "Explorer — Social-Media-Privacy-Risk-Assessment", "tree /F  (venv and caches hidden)",
                project_tree()), width=900)
            render(browser, "02_architecture_diagram.png", architecture_html(), width=1200)
            capture_app(browser, base)
            render(browser, "23_synthetic_dataset.png", dataset_html(), width=1800)
            render(browser, "24_automated_tests.png", terminal_html(
                "Terminal — pytest", "python -m pytest -v", run_pytest(["-v"])), width=1100)
            render(browser, "25_security_privacy_tests.png", terminal_html(
                "Terminal — security & privacy tests", "python -m pytest tests/test_security_privacy.py -v",
                run_pytest(["tests/test_security_privacy.py", "-v"])), width=1100)
            render(browser, "26_database_schema.png", schema_html(), width=1440)
            server.shutdown()
        if args.github or args.github_only:
            capture_github(browser)
        browser.close()


if __name__ == "__main__":
    main()
