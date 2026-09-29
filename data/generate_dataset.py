"""
Synthetic Privacy-Assessment Dataset Generator.

Creates data/social_media_privacy_assessments.csv with 1,000 FICTIONAL
privacy-assessment records.

    * No real people, no names, no usernames, no scraping, no real data.
    * Each record is a randomly generated set of questionnaire answers.
    * Every record is scored by the SAME engine the web app uses, so
      risk_score / risk_level are always consistent with the application.

How the randomness works
------------------------
Each fictional profile gets a "persona" that sets a base risk tendency:

    privacy_conscious  ~0.15   (usually picks safe answers)
    average_user       ~0.40
    casual_sharer      ~0.60
    oversharer         ~0.80   (usually picks risky answers)

For every category the tendency is jittered a little, and then each answer is
drawn with probabilities that favour answers whose risk value is close to the
tendency. This produces realistic, varied - but entirely synthetic - data.

Usage (from the project root):
    python data/generate_dataset.py
    python data/generate_dataset.py --records 2000 --seed 7
"""

import argparse
import csv
import math
import os
import random
import sys

# Allow "python data/generate_dataset.py" to import the backend package.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.assessment_engine import run_assessment  # noqa: E402
from backend.services.questionnaire import CATEGORIES, QUESTIONS, SCALES  # noqa: E402

DEFAULT_OUTPUT = os.path.join(PROJECT_ROOT, "data", "social_media_privacy_assessments.csv")

PERSONAS = {
    # name: (share of population, base risk tendency)
    "privacy_conscious": (0.20, 0.15),
    "average_user": (0.40, 0.40),
    "casual_sharer": (0.25, 0.60),
    "oversharer": (0.15, 0.80),
}

# CSV column name -> questionnaire question id
ANSWER_COLUMNS = {
    "profile_visibility": "profile_visibility",
    "phone_public": "phone_public",
    "email_public": "email_public",
    "birthday_public": "birthday_public",
    "location_public": "location_public",
    "realtime_location_sharing": "realtime_location_sharing",
    "workplace_public": "workplace_public",
    "education_public": "education_public",
    "relationship_public": "relationship_public",
    "posts_public": "posts_visibility",
    "location_tagging": "geotagging",
    "travel_posts": "travel_posts",
    "unknown_connections": "unknown_connections",
    "tag_review_enabled": "tag_review_enabled",
    "third_party_apps_reviewed": "third_party_apps_reviewed",
    "mfa_enabled": "mfa_enabled",
    "login_alerts_enabled": "login_alerts_enabled",
    "password_reuse_reported": "password_reuse",
    "suspicious_link_awareness": "suspicious_link_awareness",
    "old_posts_reviewed": "old_posts_reviewed",
    "privacy_settings_reviewed": "privacy_settings_reviewed",
}


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def _pick_answer(rng, question, tendency, spread=0.28):
    """Choose an answer, favouring options whose risk value is near `tendency`."""
    scale = SCALES[question["scale"]]
    options = question["options"]
    weights = [math.exp(-((scale[o] - tendency) ** 2) / (2 * spread ** 2)) for o in options]
    # "Not sure" is less common than a definite answer.
    weights = [w * (0.35 if o == "NOT_SURE" else 1.0) for w, o in zip(weights, options)]
    return rng.choices(options, weights=weights, k=1)[0]


def generate_profile(rng):
    """Generate one fictional set of answers. Returns (persona, answers)."""
    names = list(PERSONAS)
    persona = rng.choices(names, weights=[PERSONAS[n][0] for n in names], k=1)[0]
    base = _clamp(rng.gauss(PERSONAS[persona][1], 0.07))

    # Each category drifts a little from the base tendency.
    category_tendency = {key: _clamp(base + rng.gauss(0, 0.15)) for key in CATEGORIES}
    answers = {
        q["id"]: _pick_answer(rng, q, category_tendency[q["category"]]) for q in QUESTIONS
    }
    return persona, answers


def generate_dataset(records=1000, seed=42, output=DEFAULT_OUTPUT):
    rng = random.Random(seed)
    header = (
        ["profile_id", "synthetic_persona"]
        + list(ANSWER_COLUMNS)
        + [f"score_{cat}" for cat in CATEGORIES]
        + ["finding_count", "risk_score", "risk_level"]
    )

    os.makedirs(os.path.dirname(output), exist_ok=True)
    level_counts = {}
    with open(output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for index in range(1, records + 1):
            persona, answers = generate_profile(rng)
            result = run_assessment(answers, assessment_id=f"SYN-{index:05d}")
            level_counts[result["risk_level"]] = level_counts.get(result["risk_level"], 0) + 1
            writer.writerow(
                [f"SYN-{index:05d}", persona]
                + [answers[qid] for qid in ANSWER_COLUMNS.values()]
                + [result["category_scores"][cat] for cat in CATEGORIES]
                + [len(result["findings"]), result["overall_score"], result["risk_level"]]
            )
    return level_counts


def main():
    parser = argparse.ArgumentParser(description="Generate a synthetic privacy-assessment dataset.")
    parser.add_argument("--records", type=int, default=1000, help="number of fictional records")
    parser.add_argument("--seed", type=int, default=42, help="random seed (reproducible output)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="output CSV path")
    args = parser.parse_args()

    if args.records < 1 or args.records > 100_000:
        parser.error("--records must be between 1 and 100000")

    counts = generate_dataset(args.records, args.seed, args.output)
    print(f"Generated {args.records} synthetic records -> {args.output}")
    for level in ("LOW", "MODERATE", "HIGH", "CRITICAL"):
        print(f"  {level:<9} {counts.get(level, 0)}")


if __name__ == "__main__":
    main()
