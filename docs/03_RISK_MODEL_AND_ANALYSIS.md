# 3. Risk Model and Category Analysis

> Covers brief sections 5–21: synthetic dataset, feature engineering, category scoring, the scoring engine, the ten category analyses, findings, recommendations, the improvement simulator and the category chart.

---

## 5. Synthetic Profile Dataset

**File:** `data/social_media_privacy_assessments.csv` (1,000 rows) · **Generator:** `data/generate_dataset.py`

```bash
python data/generate_dataset.py                     # 1,000 records, seed 42 (reproducible)
python data/generate_dataset.py --records 2000 --seed 7
```

- **Entirely fictional.** IDs look like `SYN-00001`. There are no names, usernames, contact details or real data of any kind.
- Each record gets a **persona** that sets a base risk tendency: `privacy_conscious` (20%, ~0.15), `average_user` (40%, ~0.40), `casual_sharer` (25%, ~0.60), `oversharer` (15%, ~0.80). The tendency drifts per category (Gaussian jitter), and each answer is drawn with probabilities favouring options whose risk value is near that tendency.
- **All 53 answers** are generated and scored by the **same engine as the web app**, so `risk_score` and `risk_level` are always consistent with the application.

**Columns:** `profile_id, synthetic_persona, profile_visibility, phone_public, email_public, birthday_public, location_public, realtime_location_sharing, workplace_public, education_public, relationship_public, posts_public, location_tagging, travel_posts, unknown_connections, tag_review_enabled, third_party_apps_reviewed, mfa_enabled, login_alerts_enabled, password_reuse_reported, suspicious_link_awareness, old_posts_reviewed, privacy_settings_reviewed, score_<10 categories>, finding_count, risk_score, risk_level`

**Generated distribution (seed 42):** LOW 151 · MODERATE 244 · HIGH 395 · CRITICAL 210 · mean score 47.9.

---

## 6. Privacy Feature Engineering: `extract_privacy_features()`

`backend/services/assessment_engine.py`

Every answer is converted to a **risk value between 0.0 and 1.0** using its answer scale (`backend/services/questionnaire.py`):

| Scale | Example question | Mapping |
|---|---|---|
| EXPOSURE_YN | Is your phone number public? | YES 1.0 · NO 0.0 · NOT_SURE 0.6 |
| EXPOSURE | Do you post travel plans? | YES 1.0 · SOMETIMES 0.5 · NO 0.0 · NOT_SURE 0.6 |
| PROTECTIVE_YN | Is MFA enabled? | YES 0.0 · NO 1.0 · NOT_SURE 0.7 |
| PROTECTIVE | Do you review connected apps? | YES 0.0 · SOMETIMES 0.5 · NO 1.0 · NOT_SURE 0.7 |
| VISIBILITY | Default post audience | PUBLIC 1.0 · FRIENDS 0.4 · PRIVATE 0.0 · NOT_SURE 0.6 |
| FREQUENCY | Accept unknown requests? | ALWAYS 1.0 · OFTEN 0.75 · SOMETIMES 0.4 · NEVER 0.0 |
| RECENCY | Last privacy-settings review | ≤3 months 0.0 · ≤1 year 0.3 · >1 year 0.7 · NEVER 1.0 |

`NOT_SURE` is moderate risk on purpose: a setting you cannot confirm should not be relied on. Protective controls score `NOT_SURE` slightly higher (0.7), because an unknown control is usually an unconfigured one.

```python
>>> extract_privacy_features(answers)["features"]
{"phone_public": 1.0,        # public phone -> high exposure contribution
 "mfa_enabled": 1.0,         # MFA disabled -> account-security risk contribution
 "unknown_connections": 0.75,# often accepts strangers -> social-engineering contribution
 "tag_review_enabled": 1.0,  # no tag review -> content/privacy contribution
 "third_party_apps_reviewed": 1.0,  # never reviewed -> application-access risk
 ...}
```

Each question also carries a **weight** (importance inside its category, 1.0–3.0) and an **impact** (HIGH / MEDIUM / LOW). The full list is in [02_PRIVACY_QUESTIONNAIRE.md](02_PRIVACY_QUESTIONNAIRE.md).

---

## 7. Category-wise Privacy Scoring

```
category_score = round( 100 × Σ(weight_q × risk_q) / Σ(weight_q) )        0 = lower risk, 100 = higher risk
```

| Category | Brief name | Questions |
|---|---|---|
| A `profile_exposure` | Profile Exposure Score | 5 |
| B `personal_information` | Personal Information Score | 7 |
| C `location_exposure` | Location Exposure Score | 6 |
| D `content_exposure` | Content Exposure Score | 5 |
| E `connection_risk` | Connection Risk Score | 4 |
| F `tagging_risk` | Tagging Risk Score | 4 |
| G `account_security` | Account Security Score | 6 |
| H `third_party_apps` | Third-Party App Risk Score | 4 |
| I `social_engineering` | Social Engineering Score | 6 |
| J `digital_footprint` | Digital Footprint Score | 6 |

**Worked example (test TC21):** only "phone public = YES". Personal-information weights sum to 3 + 2 + 2.5 + 3 + 1.5 + 1 + 1.5 = 14.5, so the score is 100 × 3 / 14.5 = **21**. Every other category stays at 0.

---

## 8. Privacy Risk Scoring Engine: `calculate_privacy_risk()`

`backend/services/scoring_engine.py`

```
overall = round( Σ(W_c × category_score_c) / Σ(W_c) )
```

| Category | Weight |
|---|---|
| Profile Visibility | 10% |
| Personal Information | 15% |
| Location Privacy | 15% |
| Posts & Content | 10% |
| Connections | 10% |
| Tagging | 5% |
| Account Security | 15% |
| Third-Party Apps | 5% |
| Social Engineering | 10% |
| Digital Footprint | 5% |
| **Total** | **100%** |

| Score | Level |
|---|---|
| 0–20 | LOW |
| 21–40 | MODERATE |
| 41–70 | HIGH |
| 71–100 | CRITICAL |

**Configurable:** `calculate_privacy_risk(scores, weights={...}, thresholds=[...])`. Custom weights are validated (known categories only, no negatives, not all zero) and normalised to 100.

> ⚠️ **The weights and thresholds are educational assumptions.** They were chosen to be simple to explain, not fitted to real incident data. Before any professional risk decision they would need validation, for example calibration against incident data, expert review (Delphi method) or sensitivity analysis.

A **linear, transparent** model was chosen deliberately: every point of the score can be traced back to specific answers, which matters for explaining results to users and auditors. The trade-off is that it cannot capture interactions, such as "public workplace *and* public phone" being worse than the sum of the two.

---

## 9. Profile Visibility Analysis (Category A)

Questions: profile audience (PUBLIC / FRIENDS / PRIVATE), search-engine indexing, friends-list visibility, discoverability by phone/email, identifiable profile photo.

**Visibility is not automatically unsafe.** Public profiles are normal for creators, job seekers and businesses. Visibility is a *multiplier*: it decides how many people can read every other piece of information. That's why it's weighted and scored separately from *what* is exposed. A public profile with nothing sensitive on it scores in Category A, but not in Category B.

## 10. Personal Information Exposure (Category B)

Phone, personal email, full birth date, home-related info, workplace, education, relationship/family.

**We never ask for the value, only whether it's visible.** The questionnaire, validator and database physically cannot hold a phone number: only the answer codes `YES / NO / NOT_SURE` are accepted. This is data minimisation applied at the input.

## 11. Location Privacy Analysis (Category C)

Public city/hometown, real-time location sharing, geotagging frequency, real-time check-ins, travel plans, routine patterns.

**Late posting:** sharing a photo *after* leaving a place reduces immediate exposure compared with broadcasting live location, because nobody can act on "she is here right now". It doesn't erase the history, so repeated patterns still reveal routines. **The application performs no geolocation or tracking of any kind.**

## 12. Photo & Metadata Awareness

Photos can reveal location context (landmarks, street signs), workplace or school (logos, uniforms, ID badges), vehicles (plates), documents and computer screens, family members and travel. **EXIF metadata** is data stored inside an image file: camera model, date/time, sometimes **GPS coordinates**. Many platforms strip it on upload, but originals shared by email, chat or cloud links often keep it.

**Safe local viewer:** `tools/photo_metadata_viewer.py` (see [07_SECURITY_AWARENESS.md](07_SECURITY_AWARENESS.md)) reads metadata locally, shows only what's explicitly present, never uploads anything, never infers location from pixels, and can write a metadata-free *copy*.

## 13. Social Engineering Risk (Category I)

Link checking, responding to unknown DMs, sharing verification codes, verifying urgent "friend" requests, giveaways, sharing personal details in DMs. **Accepting unknown connections** lives in Category E but feeds this risk too. Public context (employer, school, travel, family) makes scam messages more convincing. See [07_SECURITY_AWARENESS.md](07_SECURITY_AWARENESS.md). No attack scripts or example scam messages are included.

## 14. Account Security Assessment (Category G)

MFA, password reuse, password manager, login alerts, recovery info reviewed, active sessions reviewed. *Unknown devices* are covered by the sessions question. These are the ten "Security controls" shown on the results page and dashboard.

**Overlap but not identical:** a compromised account breaks privacy (everything private becomes readable), and exposed data weakens security (recovery questions, targeted phishing). But each can be strong while the other is weak.

## 15. Third-Party Application Risk (Category H)

Reviewing connected apps, unused apps still connected, "Sign in with social account" usage, permissions granted to quiz/game apps.

**Principle of Least Privilege:** every app should hold only the minimum access it needs, only for as long as it needs it. Recommendation: regularly review and revoke unnecessary access.

## 16. Tagging & Mention Privacy (Category F)

Anyone can tag you, tag review, tagged posts auto-appearing, mentions from unknown accounts. **Other people's content can expose you even if you post very little**: a friend's geotagged group photo reveals where you were and who you were with.

## 17. Digital Footprint Analysis (Category J)

Old posts reviewed, old/unused accounts, public comments, privacy-settings review recency, same username everywhere, self-search. Only **self-reported practices** are evaluated. The app does not search for or measure anyone's actual footprint. Recommendation: a periodic privacy review every 3–6 months.

---

## 18. Risk Findings Engine: `generate_privacy_findings()`

`backend/services/findings_engine.py`. A finding is raised for every answer with risk ≥ 0.5.

| Impact | Risk value | Severity |
|---|---|---|
| HIGH | ≥ 0.75 | HIGH |
| HIGH | < 0.75 | MEDIUM |
| MEDIUM | ≥ 0.75 | MEDIUM |
| other | – | LOW |

Ranking: `severity × 1000 + risk × question weight × category weight`.

**Real output for the fictional demo profile** (`python tools/run_demo.py`):

```
OVERALL PRIVACY RISK: 82/100
LEVEL:                CRITICAL

TOP RISKS
  1. [HIGH] Phone number reported as publicly visible
  2. [HIGH] Real-time location sharing enabled for a broad audience
  3. [HIGH] Multi-factor authentication (MFA) is disabled
  4. [HIGH] Travel plans shared publicly before or during trips
  5. [HIGH] Real-time check-ins posted while still at the location

CATEGORY SCORES
  Profile Visibility 100 · Personal Information 78 · Location 85 · Content 82 · Connections 91
  Tagging 100 · Account Security 90 · Third-Party Apps 76 · Social Engineering 34 · Digital Footprint 96
```

## 19. Security Recommendation Engine: `generate_recommendations()`

`backend/services/recommendation_engine.py`. One recommendation per finding, so the list is personalised.

| Severity | Priority |
|---|---|
| HIGH | IMMEDIATE |
| MEDIUM | IMPORTANT |
| LOW | GOOD PRACTICE |

MFA disabled, password reuse and sharing verification codes are **always IMMEDIATE** (direct account-takeover paths).

| Risk | Recommendation |
|---|---|
| Phone number publicly visible | Limit phone-number visibility to "Only me" where possible. |
| MFA disabled | Enable MFA using the strongest supported method (security key or authenticator app over SMS). |
| Real-time location sharing | Avoid publicly broadcasting real-time location unless intentionally needed. |
| Unknown connection requests | Verify unfamiliar profiles before accepting connections; decline when unsure. |

## 20. Privacy Improvement Simulator

`backend/services/improvement_simulator.py` · `POST /api/assessment/simulate-improvement`

The simulator applies proposed changes (explicit answers, or "set these findings to their safest answer"), re-runs the **same** engine, and returns before/after, the per-category deltas and the changes applied. **Nothing is stored.**

**Demo profile with the brief's improvements** (phone, birthday, location and travel → private; unknown requests → verify; tag review, MFA and login alerts → on; apps → reviewed):

```
CURRENT:   82/100  CRITICAL
SIMULATED: 53/100  HIGH
RISK REDUCTION: 29 points
(Applying ALL recommendations: 2/100 LOW)
```

> *Framework simulation only. The simulated score shows how this educational model reacts to the changes. It is not a guarantee of real-world privacy or account safety.*

The demo stays HIGH after 11 changes because the profile also has public posts, public friends lists, frequent geotags, no follower approval, old accounts and more. That's a useful teaching point: privacy is many small settings, not one switch.

## 21. Privacy Radar / Category Chart

A horizontal **bar chart** (Chart.js) of the ten category scores, with each bar coloured by its risk level. The legend and a "Show data as a table" view carry the same information without colour. A bar chart was chosen over a radar chart because bars are compared along a common baseline, which people read more accurately than radar spokes. The same chart type is used for before/after comparisons in the simulator.
