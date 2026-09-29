"""
Safe Demonstration - runs the fictional "Demo Riya" profile end to end.

    python tools/run_demo.py

1. Assesses the fictional over-sharing profile (backend/services/demo_profiles.py)
2. Prints the overall score, category scores, top findings and recommendations
3. Simulates the improvements from the project brief
4. Writes reports/demo_privacy_report.html (open it and Print -> Save as PDF)

Everything here is fictional; no real person or account is involved.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.assessment_engine import run_assessment  # noqa: E402
from backend.services.demo_profiles import DEMO_IMPROVEMENTS, DEMO_PROFILE  # noqa: E402
from backend.services.improvement_simulator import simulate_improvement  # noqa: E402
from backend.services.questionnaire import CATEGORIES  # noqa: E402
from backend.services.report_generator import render_report_html  # noqa: E402

LINE = "=" * 64


def main():
    result = run_assessment(DEMO_PROFILE, assessment_id="demo" + "0" * 28)

    print(LINE)
    print(" SAFE DEMONSTRATION PROFILE (fictional)")
    print(LINE)
    print(f" OVERALL PRIVACY RISK: {result['overall_score']}/100")
    print(f" LEVEL:                {result['risk_level']}")
    print(f" FINDINGS:             {len(result['findings'])}")
    print(f" CONTROLS ENABLED:     {result['security_controls']['enabled_count']}"
          f"/{result['security_controls']['total']}")

    print("\n CATEGORY SCORES")
    for key, score in result["category_scores"].items():
        bar = "#" * (score // 5)
        print(f"  {CATEGORIES[key]['name']:<36} {score:>3}/100  {bar}")

    print("\n TOP RISKS")
    for i, finding in enumerate(result["top_findings"], start=1):
        print(f"  {i}. [{finding['severity']}] {finding['title']}")

    print("\n TOP RECOMMENDATIONS")
    for rec in result["recommendations"][:8]:
        print(f"  [{rec['priority']}] {rec['recommendation']}")

    sim = simulate_improvement(DEMO_PROFILE, changes=DEMO_IMPROVEMENTS)
    print("\n" + LINE)
    print(" PRIVACY IMPROVEMENT SIMULATION")
    print(LINE)
    print(f" CURRENT:   {sim['current']['overall_score']}/100  {sim['current']['risk_level']}")
    for change in sim["changes_applied"]:
        print(f"   + {change['question_id']}: {change['from']} -> {change['to']}")
    print(f" SIMULATED: {sim['simulated']['overall_score']}/100  {sim['simulated']['risk_level']}")
    print(f" RISK REDUCTION: {sim['risk_reduction']} points")

    full = simulate_improvement(DEMO_PROFILE, fix_findings="ALL")
    print(f" (Applying ALL recommendations: {full['simulated']['overall_score']}/100 "
          f"{full['simulated']['risk_level']})")
    print(f"\n {sim['disclaimer']}")

    reports_dir = os.path.join(PROJECT_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, "demo_privacy_report.html")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(render_report_html(result))
    print(f"\n Report written: {path}")


if __name__ == "__main__":
    main()
