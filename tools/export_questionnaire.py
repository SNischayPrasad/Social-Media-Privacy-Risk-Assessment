"""
Export the questionnaire definition to docs/02_PRIVACY_QUESTIONNAIRE.md.

    python tools/export_questionnaire.py

The documentation is generated from backend/services/questionnaire.py so the
docs always match the code (single source of truth).
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.questionnaire import ANSWER_LABELS, CATEGORIES, QUESTIONS, SCALES  # noqa: E402

OUTPUT = os.path.join(PROJECT_ROOT, "docs", "02_PRIVACY_QUESTIONNAIRE.md")


def main():
    lines = [
        "# Privacy Assessment Questionnaire",
        "",
        "> Auto-generated from `backend/services/questionnaire.py` by `tools/export_questionnaire.py`.",
        "",
        f"**{len(QUESTIONS)} questions in {len(CATEGORIES)} categories.** "
        "No question asks for the sensitive value itself (for example, the phone number). "
        "Each question asks only whether something is visible or enabled.",
        "",
        "## How answers are scored",
        "",
        "Every answer maps to a risk value between 0.0 (no added risk) and 1.0 (maximum added risk).",
        "",
        "| Scale | Used for | Answer -> risk value |",
        "|---|---|---|",
    ]
    usage = {
        "EXPOSURE": "Is X visible / do you do X? (with Sometimes)",
        "EXPOSURE_YN": "Is X visible? (yes/no)",
        "PROTECTIVE": "Do you use control X? (with Sometimes; NO is risky)",
        "PROTECTIVE_YN": "Is control X enabled? (NO is risky)",
        "VISIBILITY": "Audience settings",
        "FREQUENCY": "How often do you do X?",
        "RECENCY": "When did you last review X?",
    }
    for name, scale in SCALES.items():
        mapping = ", ".join(f"{ANSWER_LABELS[a]} = {v}" for a, v in scale.items())
        lines.append(f"| `{name}` | {usage[name]} | {mapping} |")
    lines += [
        "",
        "`Not sure` is scored as moderate risk on purpose: you cannot rely on a setting you cannot confirm.",
        "",
        "**Weight** is the question's importance inside its category (1.0-3.0). **Impact** is the potential "
        "harm if the weakness is abused and drives finding severity.",
        "",
    ]

    number = 0
    for key, meta in CATEGORIES.items():
        lines += [f"## Category {meta['code']}: {meta['name']}", "", meta["description"], "",
                  "| # | Question | Answers | Weight | Impact | Feature id |", "|---|---|---|---|---|---|"]
        for q in (q for q in QUESTIONS if q["category"] == key):
            number += 1
            answers = " / ".join(ANSWER_LABELS[o].upper() for o in q["options"])
            lines.append(f"| {meta['code']}{number} | {q['text']} | {answers} | {q['weight']} | "
                         f"{q['impact']} | `{q['id']}` |")
        lines.append("")

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    print(f"Wrote {OUTPUT} ({number} questions)")


if __name__ == "__main__":
    main()
