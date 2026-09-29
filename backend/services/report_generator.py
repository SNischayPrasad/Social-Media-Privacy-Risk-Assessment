"""
Privacy Assessment Report generator (HTML, printable to PDF).

SAFE REPORT GENERATION
    * The report is built only from the assessment RESULT (scores, finding
      types, recommendations). No raw answers and no personal data exist in it.
    * Every dynamic value is passed through html.escape() so that nothing can
      inject HTML or JavaScript (XSS protection), even if data were tampered with.
    * The report contains no JavaScript at all; it is served with a strict
      Content-Security-Policy (see utils/security.py).

To create a PDF, open the report in a browser and use Print -> "Save as PDF".
"""

from html import escape

from backend.services.checklist import get_checklist
from backend.services.questionnaire import CATEGORIES

LEVEL_COLOURS = {
    "LOW": "#1f8a4c",
    "MODERATE": "#b7791f",
    "HIGH": "#c2410c",
    "CRITICAL": "#b91c1c",
}
PRIORITY_LABELS = {
    "IMMEDIATE": "Immediate",
    "IMPORTANT": "Important",
    "GOOD_PRACTICE": "Good practice",
}

REPORT_CSS = """
body{font-family:Segoe UI,Arial,sans-serif;color:#1f2933;max-width:900px;margin:32px auto;padding:0 20px;line-height:1.5}
h1{font-size:26px;margin-bottom:4px}h2{font-size:19px;border-bottom:2px solid #e4e7eb;padding-bottom:4px;margin-top:32px}
.meta{color:#52606d;font-size:14px}.score{display:flex;gap:24px;align-items:center;margin:20px 0}
.big{font-size:56px;font-weight:700}.pill{display:inline-block;padding:4px 12px;border-radius:999px;color:#fff;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:7px 8px;border-bottom:1px solid #e4e7eb;vertical-align:top}
th{background:#f5f7fa}.bar{background:#e4e7eb;border-radius:4px;height:10px;width:100%}.bar span{display:block;height:10px;border-radius:4px}
.sev-HIGH{color:#b91c1c;font-weight:600}.sev-MEDIUM{color:#c2410c;font-weight:600}.sev-LOW{color:#52606d;font-weight:600}
.box{border:1px solid #e4e7eb;border-radius:8px;padding:14px 16px;background:#fafbfc}
.disclaimer{font-size:13px;color:#52606d;border-left:4px solid #b7791f;padding:8px 12px;background:#fffaf0}
ul.check{list-style:none;padding-left:0}ul.check li{padding:4px 0}ul.check li:before{content:"\\2610  ";font-size:16px}
.rel{font-weight:600}.foot{margin-top:40px;font-size:12px;color:#7b8794}
@media print{body{margin:0}h2{page-break-after:avoid}table,.box{page-break-inside:avoid}}
"""


def _bar(score):
    colour = "#1f8a4c" if score <= 20 else "#b7791f" if score <= 40 else "#c2410c" if score <= 70 else "#b91c1c"
    return f'<div class="bar"><span style="width:{int(score)}%;background:{colour}"></span></div>'


def render_report_html(result):
    """Render a complete, standalone HTML privacy report for an assessment result."""
    level = result["risk_level"]
    colour = LEVEL_COLOURS.get(level, "#52606d")
    finding_types = [f["finding_type"] for f in result["findings"]]

    category_rows = "".join(
        f"<tr><td>{escape(CATEGORIES[key]['code'])}. {escape(CATEGORIES[key]['name'])}</td>"
        f"<td style='width:60px'><strong>{int(score)}</strong>/100</td>"
        f"<td style='width:45%'>{_bar(score)}</td>"
        f"<td>{escape(result['category_levels'].get(key, ''))}</td></tr>"
        for key, score in result["category_scores"].items()
    )

    top_findings = "".join(
        f"<tr><td>{i}</td><td class='sev-{escape(f['severity'])}'>{escape(f['severity'])}</td>"
        f"<td>{escape(f['title'])}</td><td>{escape(f['category_name'])}</td></tr>"
        for i, f in enumerate(result["findings"][:10], start=1)
    ) or "<tr><td colspan='4'>No significant findings.</td></tr>"

    recommendation_rows = "".join(
        f"<tr><td>{escape(PRIORITY_LABELS[r['priority']])}</td><td>{escape(r['risk'])}</td>"
        f"<td>{escape(r['recommendation'])}</td></tr>"
        for r in result["recommendations"]
    ) or "<tr><td colspan='3'>No recommendations - keep reviewing settings periodically.</td></tr>"

    immediate = [r for r in result["recommendations"] if r["priority"] == "IMMEDIATE"]
    priority_actions = "".join(f"<li>{escape(r['recommendation'])}</li>" for r in immediate[:8]) \
        or "<li>No immediate actions identified.</li>"

    controls = result["security_controls"]
    control_items = "".join(
        f"<li>{'&#10003;' if c['enabled'] else '&#10007;'} {escape(c['label'])}</li>"
        for c in controls["controls"]
    )

    checklist_items = "".join(
        f"<li class='{'rel' if item['relevant'] else ''}'>{escape(item['item'])}"
        f"{' &nbsp;<em>(relevant to your findings)</em>' if item['relevant'] else ''}</li>"
        for item in get_checklist(finding_types)
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Privacy Assessment Report {escape(result['assessment_id'][:8])}</title>
<style>{REPORT_CSS}</style></head>
<body>
<h1>Social Media Privacy Risk Assessment Report</h1>
<div class="meta">Assessment ID: <code>{escape(result['assessment_id'])}</code> &middot;
Assessment date (UTC): {escape(result['created_at'])} &middot; Framework v1.0</div>

<div class="score">
  <div class="big" style="color:{colour}">{int(result['overall_score'])}<span style="font-size:22px;color:#7b8794">/100</span></div>
  <div><div class="pill" style="background:{colour}">{escape(level)} RISK</div>
  <div class="meta" style="margin-top:6px">{len(result['findings'])} findings &middot;
  {len(result['high_risk_categories'])} high-risk categories &middot;
  {controls['enabled_count']}/{controls['total']} security controls enabled</div></div>
</div>
<p class="meta">Scale: 0-20 Low &middot; 21-40 Moderate &middot; 41-70 High &middot; 71-100 Critical.
Higher scores mean higher assessed exposure.</p>

<h2>Category Scores</h2>
<table><tr><th>Category</th><th>Score</th><th>Risk</th><th>Level</th></tr>{category_rows}</table>

<h2>Top Findings</h2>
<table><tr><th>#</th><th>Severity</th><th>Finding</th><th>Category</th></tr>{top_findings}</table>

<h2>Priority Actions</h2>
<div class="box"><ol>{priority_actions}</ol></div>

<h2>Security Recommendations</h2>
<table><tr><th>Priority</th><th>Risk</th><th>Recommendation</th></tr>{recommendation_rows}</table>

<h2>Security Controls</h2>
<ul>{control_items}</ul>

<h2>Privacy Checklist</h2>
<ul class="check">{checklist_items}</ul>

<h2>Disclaimer</h2>
<p class="disclaimer">{escape(result['disclaimer'])}</p>
<p class="meta">This report contains no personal information: no names, contact details, birth dates,
addresses, passwords, locations or questionnaire answers - only scores and finding categories.</p>

<div class="foot">Generated by the Social Media Privacy Risk Assessment Framework (educational project).
To save as PDF: use your browser's Print &rarr; Save as PDF.</div>
</body></html>"""
