# 5. Testing Strategy and Security & Privacy Testing

> Covers brief sections 33 (Testing Strategy) and 34 (Security & Privacy Testing).

```bash
python -m pytest -v
```

**Latest run: 65 passed, 0 failed** (Python 3.13, Flask 3.1, pytest 9.1).

| File | What it covers | Tests |
|---|---|---|
| `tests/test_scoring_engine.py` | Questionnaire, feature extraction, category and overall scoring, boundaries, findings, recommendations, simulator | 36 |
| `tests/test_api.py` | REST endpoints, database save/retrieve, reports, dashboard, checklist, frontend serving | 11 |
| `tests/test_security_privacy.py` | Data minimisation, deletion, retention, validation, XSS, headers, rate limiting, errors, env config | 15 |
| `tests/test_dataset_and_tools.py` | Synthetic dataset generator, reproducibility, photo metadata viewer | 3 |

Every test builds a fresh app with a **temporary SQLite database** (`tests/conftest.py`), so tests never touch real data and don't depend on each other. Single-weakness tests start from a **fully private profile** and change only the answer under test (`profile_with(...)`), which isolates cause and effect.

---

## 33. Functional Test Cases

"Actual Result" was recorded from the latest `pytest -v` run.

| Test ID | Scenario | Input | Expected Result | Actual Result | Pass/Fail |
|---|---|---|---|---|---|
| TC01 | Fully private profile | Safest answer for all 53 questions | Score 0, LOW, no findings, 10/10 controls | Score 0, LOW, 0 findings, 10/10 | ✅ Pass |
| TC02 | Fully public synthetic profile | Riskiest answer for all 53 | Score 100, CRITICAL, all categories 100, 53 findings | As expected | ✅ Pass |
| TC03 | Public phone | `phone_public=YES` | Personal-info score > 0; HIGH finding; IMMEDIATE rec | As expected | ✅ Pass |
| TC04 | Public email | `email_public=YES` | `email_public` finding; personal-info > 0 | As expected | ✅ Pass |
| TC05 | Public birthday | `birthday_public=YES` | MEDIUM finding | MEDIUM | ✅ Pass |
| TC06 | Public location | `location_public=YES` | Finding; location score > 0 | As expected | ✅ Pass |
| TC07 | Real-time check-ins | `realtime_checkins=ALWAYS`, `realtime_location_sharing=YES` | Both HIGH findings | Both HIGH | ✅ Pass |
| TC08 | Travel plans | `travel_posts=YES` | HIGH finding | HIGH | ✅ Pass |
| TC09 | Workplace exposure | `workplace_public=YES` | Finding raised | Raised | ✅ Pass |
| TC10 | Education exposure | `education_public=YES` | LOW finding; GOOD_PRACTICE rec | As expected | ✅ Pass |
| TC11 | Public posts | `posts_visibility=PUBLIC` vs `FRIENDS` | Public > Friends > 0 | As expected | ✅ Pass |
| TC12 | Unknown connections | `unknown_connections=ALWAYS` | HIGH finding; connection score > 0 | As expected | ✅ Pass |
| TC13 | Tag review disabled | `tag_review_enabled=NO` | Finding; tagging score = 100×3/7.5 = 40 | 40 | ✅ Pass |
| TC14 | MFA disabled | `mfa_enabled=NO` | HIGH finding; IMMEDIATE; control shows off | As expected | ✅ Pass |
| TC15 | Login alerts disabled | `login_alerts_enabled=NO` | Finding raised | Raised | ✅ Pass |
| TC16 | Password reuse reported | `password_reuse=YES` | IMMEDIATE recommendation | IMMEDIATE | ✅ Pass |
| TC17 | Third-party apps not reviewed | `third_party_apps_reviewed=NO` | Finding; third-party score > 0 | As expected | ✅ Pass |
| TC18 | Low suspicious-link awareness | `suspicious_link_awareness=NO` | HIGH finding | HIGH | ✅ Pass |
| TC19 | Old posts not reviewed | `old_posts_reviewed=NO` | Finding; footprint score > 0 | As expected | ✅ Pass |
| TC20 | Privacy settings not reviewed | `NEVER` vs `WITHIN_YEAR` | Finding for NEVER; none for WITHIN_YEAR (0.3 < 0.5) | As expected | ✅ Pass |
| TC21 | Category score calculation | Only phone public | Personal info = round(100×3/14.5) = 21; others 0 | 21 | ✅ Pass |
| TC22 | Overall score calculation | Account security 100, location 60, others 0 | (15×100 + 15×60)/100 = 24 → MODERATE; high-risk = [account_security, location] | 24, MODERATE | ✅ Pass |
| TC23 | Score boundary 20 | 0, 20, 21 | LOW, LOW, MODERATE | As expected | ✅ Pass |
| TC24 | Score boundary 40 | 40, 41 | MODERATE, HIGH | As expected | ✅ Pass |
| TC25 | Score boundary 70 | 70, 71, 100 | HIGH, CRITICAL, CRITICAL | As expected | ✅ Pass |
| TC26 | Recommendation generation | Demo profile | One rec per finding; sorted IMMEDIATE → GOOD_PRACTICE; each has text and reason | 48 recs, ordered | ✅ Pass |
| TC27 | Improvement simulation | Demo + brief's improvements; then fix ALL | Score drops; reduction = before − after; ALL → LOW | 82 → 53; ALL → 2 (LOW) | ✅ Pass |
| TC28 | Database save | POST with `store: true`, then GET | Same score, level, category scores and finding types | Identical | ✅ Pass |
| TC29 | Sensitive data not stored | Save demo, inspect schema and full SQL dump | Only approved columns; no token plaintext; no raw answers | As expected | ✅ Pass |
| TC30 | Report generation | POST /api/report | HTML with all sections, no `<script>`, strict CSP | As expected | ✅ Pass |

**Additional functional tests:** 40+ questions in 10 categories with weights summing to 100 · "Not sure" treated as moderate risk · custom weights change the score and invalid weights are rejected · simulator rejects invalid answers and unknown findings · stateless and stored report endpoints · form-POST download · dashboard stats · checklist relevance flags · all frontend pages served · 404 for unknown assessments · dataset columns, consistency and reproducibility · metadata viewer reads GPS and strips it into a copy.

---

## 34. Security & Privacy Testing

| Check | Test | How it's verified | Why it matters |
|---|---|---|---|
| **No phone / email / address / birth date / password / location / message storage** | `test_tc29_sensitive_data_not_stored` | The schema must match an approved column allow-list exactly; no column name matches sensitive words; a full `iterdump()` of the DB must not contain raw answer codes or the plaintext deletion token | Proves data minimisation in the actual database, not just in the docs |
| Result object has no raw answers | `test_assessment_result_contains_no_raw_answers` | Result has no `responses`, `answers` or `features` keys | Nothing sensitive can leak via API responses or reports |
| **Input validation** | `test_validation_*`, `test_api_returns_400_for_invalid_input` | Missing answers, unknown keys (e.g. `phone_number`), free text (`+1 555 0100`), wrong types, non-objects and malformed JSON are all rejected with 400 | The allow-list makes it impossible to submit personal data or payloads |
| ID validation / traversal | `test_invalid_assessment_id_is_rejected` | Non-hex ids → 400; `../../etc/passwd` → 404 | Prevents path traversal and odd lookups |
| Oversized requests | `test_oversized_request_rejected` | A 40 KB body → 413 | Limits resource-exhaustion attempts |
| **XSS protection** | `test_report_escapes_html`, `test_api_returns_400_for_invalid_input` | `<img onerror>` and `<script>` injected into report data come out HTML-escaped; malicious answers aren't echoed back; frontend uses `textContent` only | Stops stored and reflected XSS |
| **Security headers** | `test_security_headers_present` | CSP (`default-src 'self'`, `frame-ancestors 'none'`), `nosniff`, `X-Frame-Options: DENY`, `no-referrer`, `no-store`, `Permissions-Policy` | Defence in depth against XSS, clickjacking and caching or leaking of results |
| **API rate limiting** | `test_rate_limiting` | Limit 3/min → responses `201, 201, 201, 429` | Slows automated abuse |
| Error handling | `test_errors_do_not_leak_stack_traces` | Bad input → 400 JSON, never a traceback | Avoids leaking internals to attackers |
| **Authentication** | n/a (by design) | The app has no accounts, so no credentials are collected. Deletion requires a secret token (see below). | Avoids storing identities at all |
| **Secure session handling** | n/a (by design) | No server sessions or cookies are used. Answers live in the browser's `sessionStorage`, which is cleared when the tab closes. | No session hijacking surface |
| **Environment variables** | `test_configuration_comes_from_environment` | Settings (rate limit, debug) come from env; debug defaults to off; host defaults to `127.0.0.1` | No secrets in code; safe defaults |
| **Safe report generation** | `test_tc30_report_generation`, `test_report_escapes_html` | Escaped output, no scripts, report CSP `default-src 'none'` | A report can't become an attack vector |
| **Data deletion** | `test_stored_data_can_be_deleted` | No token → 401; wrong token → 404; right token → 200; then GET → 404 | User control over their data |
| Retention | `test_retention_policy_purges_old_assessments` | A 90-day-old record is purged by the 30-day policy | Retention limitation |
| Dataset contains no PII | `test_synthetic_dataset_generation` | No PII columns; answer columns contain only fixed codes; IDs are `SYN-…` | Synthetic data stays synthetic |

### Manual checks performed
- Browsed all four pages in light and dark mode, and at 375 px mobile width (no horizontal scroll).
- The browser console showed no CSP violations with Chart.js (SRI-pinned) and Google Fonts allowed.
- Completed the questionnaire with the demo answers, ran the simulator, and opened the report and dashboard.
