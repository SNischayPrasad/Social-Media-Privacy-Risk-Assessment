"""
Scoring Engine - category-wise scores and the overall Privacy Risk Score.

SCORE DIRECTION: 0 = lower assessed risk, 100 = higher assessed risk/exposure.

Step 1 - Category score (0-100)
    Weighted average of the question risk values inside the category:

        category_score = 100 * sum(weight_q * risk_q) / sum(weight_q)

Step 2 - Overall score (0-100)
    Weighted average of the ten category scores using configurable weights:

        overall = sum(W_c * category_score_c) / sum(W_c)

Step 3 - Classification
    0-20 LOW | 21-40 MODERATE | 41-70 HIGH | 71-100 CRITICAL

IMPORTANT: the weights and thresholds are EDUCATIONAL ASSUMPTIONS chosen to be
easy to explain. They have not been statistically validated and must be
reviewed/calibrated before being used for any professional risk decision.
"""

from backend.services.questionnaire import CATEGORIES, QUESTIONS

# Default category weights (percent). They must add up to 100.
DEFAULT_CATEGORY_WEIGHTS = {
    "profile_exposure": 10,
    "personal_information": 15,
    "location_exposure": 15,
    "content_exposure": 10,
    "connection_risk": 10,
    "tagging_risk": 5,
    "account_security": 15,
    "third_party_apps": 5,
    "social_engineering": 10,
    "digital_footprint": 5,
}

# Upper bound (inclusive) of each risk level, checked in order.
DEFAULT_THRESHOLDS = [
    (20, "LOW"),
    (40, "MODERATE"),
    (70, "HIGH"),
    (100, "CRITICAL"),
]

RISK_LEVELS = [level for _, level in DEFAULT_THRESHOLDS]


def classify_risk(score, thresholds=None):
    """Map a 0-100 score to LOW / MODERATE / HIGH / CRITICAL."""
    for upper, level in thresholds or DEFAULT_THRESHOLDS:
        if score <= upper:
            return level
    return (thresholds or DEFAULT_THRESHOLDS)[-1][1]


def calculate_category_scores(features):
    """Compute a 0-100 score for each of the ten categories.

    Args:
        features: {question_id: risk_value 0.0-1.0} from extract_privacy_features().

    Returns:
        {category_key: int score 0-100}
    """
    totals = {key: 0.0 for key in CATEGORIES}
    weight_sums = {key: 0.0 for key in CATEGORIES}

    for question in QUESTIONS:
        category = question["category"]
        totals[category] += question["weight"] * features[question["id"]]
        weight_sums[category] += question["weight"]

    return {
        key: int(round(100 * totals[key] / weight_sums[key])) if weight_sums[key] else 0
        for key in CATEGORIES
    }


def validate_weights(weights):
    """Check a custom weight dictionary and return it normalised to sum to 100.

    Raises ValueError for unknown categories, negative numbers or an all-zero set.
    """
    unknown = set(weights) - set(CATEGORIES)
    if unknown:
        raise ValueError(f"Unknown categories in weights: {', '.join(sorted(unknown))}")

    merged = {key: float(weights.get(key, 0)) for key in CATEGORIES}
    if any(value < 0 for value in merged.values()):
        raise ValueError("Weights cannot be negative.")
    total = sum(merged.values())
    if total <= 0:
        raise ValueError("At least one weight must be greater than zero.")
    return {key: round(100 * value / total, 2) for key, value in merged.items()}


def calculate_privacy_risk(category_scores, weights=None, thresholds=None):
    """Combine category scores into the overall Privacy Risk Score.

    Args:
        category_scores: {category_key: 0-100}.
        weights: optional {category_key: weight}; normalised automatically.
        thresholds: optional list of (upper_bound, level) tuples.

    Returns:
        dict with overall_score, risk_level, weights, category_levels and
        high_risk_categories (categories rated HIGH or CRITICAL).
    """
    used_weights = validate_weights(weights) if weights else dict(DEFAULT_CATEGORY_WEIGHTS)
    total_weight = sum(used_weights.values())

    weighted = sum(used_weights[key] * category_scores[key] for key in CATEGORIES)
    overall = int(round(weighted / total_weight))

    category_levels = {key: classify_risk(score, thresholds) for key, score in category_scores.items()}
    high_risk = [
        key for key, level in category_levels.items() if level in ("HIGH", "CRITICAL")
    ]
    high_risk.sort(key=lambda key: category_scores[key], reverse=True)

    return {
        "overall_score": overall,
        "risk_level": classify_risk(overall, thresholds),
        "weights": used_weights,
        "category_levels": category_levels,
        "high_risk_categories": high_risk,
    }
