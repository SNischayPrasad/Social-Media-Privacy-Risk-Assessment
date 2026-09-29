# 4. Architecture, API, Database, Dashboard and Report

> Covers brief sections 22–29: dashboard, report, safe storage, database design, REST API, system architecture, technology stack and folder structure.

---

## 27. System Architecture

```
User (browser)
 ↓
Privacy Questionnaire ............ frontend/assessment.html + js/assessment.js
 ↓   (answers kept only in this tab's sessionStorage)
Input Validation ................. backend/utils/validators.py  (allow-list)
 ↓
Feature Extraction ............... assessment_engine.extract_privacy_features()
 ↓
┌──────────────────────────────────────────┐
│ Profile Risk Analyzer          (A)       │
│ Personal Info Analyzer         (B)       │
│ Location Analyzer              (C)       │   scoring_engine.calculate_category_scores()
│ Content Analyzer               (D)       │   one weighted score per category,
│ Connection / Tagging Analyzers (E, F)    │   driven by the questionnaire definition
│ Account Security Analyzer      (G)       │
│ Third-Party App Analyzer       (H)       │
│ Social Engineering Analyzer    (I)       │
│ Digital Footprint Analyzer     (J)       │
└──────────────────────────────────────────┘
 ↓
Category Scores
 ↓
Risk Scoring Engine .............. scoring_engine.calculate_privacy_risk()  (configurable weights)
 ↓
Overall Risk + Classification
 ↓
Findings Engine .................. findings_engine.generate_privacy_findings()
 ↓
Recommendation Engine ............ recommendation_engine.generate_recommendations()
 ↓
Privacy Dashboard ................ frontend/dashboard.html  ← GET /api/dashboard/stats
 ↓
Privacy Report ................... report_generator.render_report_html()  → HTML → Print to PDF

Optional (only if the user ticks "Save my anonymous result")
 ↓
Analytics Database (SQLite) ...... scores + finding types only  → anonymous aggregates
```

**Design decisions**

- **One questionnaire definition drives everything.** The UI, validator, scoring, findings, dataset generator and docs all read `questionnaire.py`, so they can't drift apart.
- **Engines are pure functions.** `run_assessment()` never touches the database, so it's easy to unit test and reuse (the simulator and dataset generator call it too).
- **One origin.** Flask serves both the API and the static frontend, so no CORS configuration is needed.

---

## 28. Technology Stack

| | Option A: Beginner (**used**) | Option B: Modern |
|---|---|---|
| Frontend | HTML, CSS, vanilla JavaScript | React |
| Backend | Python **Flask** | FastAPI |
| Database | **SQLite** | PostgreSQL / SQLite |
| Charts | **Chart.js** (CDN, SRI-pinned) | Recharts / Chart.js |
| Reports | **HTML → browser Print to PDF** | HTML / WeasyPrint PDF |
| Tests | **pytest** | pytest + Playwright |

**Option A, advantages:** no build step and no Node.js; one `python run.py` starts everything; every file is readable by a beginner; SQLite is a single file.
**Option A, limitations:** manual DOM code gets verbose as the UI grows; the in-memory rate limiter works for a single process only; SQLite isn't meant for many concurrent writers.
**Option B, advantages:** automatic OpenAPI docs and Pydantic validation (FastAPI); component-based UI (React); scales to teams and production.
**Option B, limitations:** more tooling (npm, bundler, CORS, two servers) and more concepts to learn at once.

**Recommendation for a student:** Option A (built here). Once the concepts are solid, porting the pure-Python engines to FastAPI is a good follow-up project, because they don't depend on Flask at all.

---

## 29. Project Folder Structure

```
Social-Media-Privacy-Risk-Assessment/
├── backend/
│   ├── app.py                     Flask app factory: routes, error handlers, security headers
│   ├── config.py                  Settings from environment variables (.env)
│   ├── routes/
│   │   ├── assessment_routes.py   /api/questionnaire, /api/assessment..., /api/report
│   │   └── dashboard_routes.py    /api/dashboard/stats, /api/privacy-checklist, /api/health
│   ├── models/
│   │   └── database.py            SQLite schema + data access (privacy-first)
│   ├── services/
│   │   ├── questionnaire.py       53 questions, answer scales, weights (single source of truth)
│   │   ├── assessment_engine.py   extract_privacy_features(), run_assessment()
│   │   ├── scoring_engine.py      category scores, calculate_privacy_risk(), classify_risk()
│   │   ├── findings_engine.py     generate_privacy_findings(), security controls
│   │   ├── recommendation_engine.py  generate_recommendations(), recommendation catalog
│   │   ├── improvement_simulator.py  simulate_improvement()
│   │   ├── report_generator.py    render_report_html() - escaped, script-free
│   │   ├── dashboard_service.py   aggregate statistics from the synthetic dataset
│   │   ├── checklist.py           privacy checklist
│   │   └── demo_profiles.py       fictional demo profile + fully private/public profiles
│   └── utils/
│       ├── validators.py          allow-list input validation
│       └── security.py            CSP & security headers, rate limiter
├── frontend/
│   ├── index.html                 overview page (demo profile, concepts)
│   ├── assessment.html            questionnaire, results, simulator, report buttons
│   ├── dashboard.html             your result + synthetic aggregate charts
│   ├── checklist.html             printable privacy checklist
│   ├── css/styles.css
│   └── js/                        common.js, home.js, assessment.js, dashboard.js, checklist.js
├── data/
│   ├── generate_dataset.py        synthetic dataset generator
│   └── social_media_privacy_assessments.csv
├── tools/
│   ├── run_demo.py                safe demonstration (section 32)
│   ├── photo_metadata_viewer.py   local EXIF viewer / remover (section 12)
│   └── export_questionnaire.py    regenerates docs/02_PRIVACY_QUESTIONNAIRE.md
├── reports/                       generated reports (demo report committed)
├── tests/                         65 automated tests (pytest)
├── screenshots/                   portfolio screenshots (see screenshots/README.md)
├── docs/                          all documentation
├── run.py                         start the app: python run.py
├── README.md
├── requirements.txt
├── .env.example
└── .gitignore
```

| Folder | Why it exists |
|---|---|
| `backend/routes` | HTTP layer only: parse the request, call a service, return JSON. No business logic. |
| `backend/services` | All privacy logic, as pure functions. Framework-independent and unit-tested. |
| `backend/models` | The only code that talks to SQLite. |
| `backend/utils` | Cross-cutting security (validation, headers, rate limiting). |
| `frontend` | Static pages; no build step. |
| `data` | Synthetic data and its generator. |
| `tools` | Command-line utilities for demos and documentation. |
| `reports` | Output folder for HTML reports (git-ignored except the demo). |
| `tests` | Automated functional, API, security and privacy tests. |
| `screenshots` | Portfolio evidence. |
| `docs` | Explanations, design, testing, report and career material. |

---

## 22. Dashboard

`frontend/dashboard.html` + `GET /api/dashboard/stats`

**Top cards** (from your latest assessment in this browser tab): Overall Risk Score · Risk Level · High-Risk Categories · Recommendations · Security Controls Enabled. If there's no assessment yet, the cards are replaced by a **Start privacy assessment** button.

**Charts** (each with a "Show data as a table" view):
1. Category risk scores: your assessment vs synthetic average
2. Privacy risk distribution: synthetic records per level
3. Top privacy weaknesses: % of synthetic records
4. Account security controls: adoption %
5. Digital footprint risk: score distribution
6. Privacy improvement comparison: from your latest simulation

---

## 23. Privacy Report

`backend/services/report_generator.py`. Available from `POST /api/report` (stateless, from answers) or `GET /api/assessment/{id}/report` (saved result).

Contents: Assessment ID · Assessment Date · Overall Risk · Risk Level · Category Scores · Top Findings · Priority Actions · Security Recommendations · Security Controls · Privacy Checklist · Disclaimer.

- **No sensitive information:** built only from scores and finding types. It contains no answers, names or contact details.
- Every dynamic value is `html.escape()`d, the report contains no JavaScript, and it's served with `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'`.
- **Export:** HTML download, or open → browser *Print → Save as PDF* (print stylesheet included). A demo report is in `reports/demo_privacy_report.html`.

---

## 24. Safe Data Storage

**Stored (only if the user opts in):** `assessment_id`, `overall_score`, `risk_level`, `created_at`, category scores, finding types (with severity and a generic description), and the SHA-256 hash of a deletion token.

**Never stored:** phone numbers, email addresses, home addresses, birth dates, passwords, exact locations, private messages, IP addresses, names or usernames. **Raw questionnaire answers aren't stored either.**

| Principle | How it's applied |
|---|---|
| **Data minimisation** | The questionnaire asks *whether* data is visible, never the data. The database has no column that could hold PII or answers (verified by test TC29). |
| **Purpose limitation** | Stored results are used only for the user's own report and anonymous aggregate counts. There's no marketing, profiling or sharing. |
| **Privacy by design** | Privacy is built into the schema, the API (store defaults to `false`), validation, the report and retention. It isn't bolted on afterwards. |

---

## 25. Database Design (SQLite)

```sql
ASSESSMENTS      (assessment_id TEXT PK, overall_score INT 0-100, risk_level TEXT, created_at TEXT, delete_token_hash TEXT)
CATEGORY_SCORES  (category_score_id INT PK, assessment_id FK → ASSESSMENTS ON DELETE CASCADE, category TEXT, score INT 0-100)
FINDINGS         (finding_id INT PK, assessment_id FK → ASSESSMENTS ON DELETE CASCADE, category TEXT,
                  finding_type TEXT, severity TEXT, description TEXT)
RECOMMENDATIONS  (recommendation_id INT PK, finding_type TEXT UNIQUE, recommendation TEXT, priority TEXT)   -- static catalog
```

```
ASSESSMENTS 1 ──< CATEGORY_SCORES
ASSESSMENTS 1 ──< FINDINGS >── (finding_type) ── RECOMMENDATIONS
```

- `CHECK` constraints enforce score ranges and allowed levels, severities and priorities.
- `ON DELETE CASCADE` means deleting an assessment removes all its rows.
- `delete_token_hash` stores only a hash, never the token itself.
- All SQL uses `?` placeholders (parameterised queries), which prevents SQL injection.

---

## 26. REST API Design

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/questionnaire` | Questionnaire (categories, questions, allowed answers, category weights) |
| GET | `/api/demo-profile` | Fictional demo answers |
| POST | `/api/assessment` | Run an assessment; stores only if `"store": true` |
| GET | `/api/assessment/{id}` | Saved (minimised) assessment |
| GET | `/api/assessment/{id}/recommendations` | Recommendations for a saved assessment |
| DELETE | `/api/assessment/{id}` | Delete a saved assessment (header `X-Delete-Token`) |
| POST | `/api/assessment/simulate-improvement` | What-if simulation (nothing stored) |
| POST | `/api/report` | Printable HTML report from answers (nothing stored) |
| GET | `/api/assessment/{id}/report` | Printable report of a saved assessment |
| GET | `/api/dashboard/stats` | Aggregate statistics |
| GET | `/api/privacy-checklist?findings=a,b` | Checklist, with items relevant to the given findings flagged |
| GET | `/api/health` | Liveness check |

### POST /api/assessment
**Request**
```json
{ "responses": { "profile_visibility": "PUBLIC", "phone_public": "YES", "...": "all 53 questions" },
  "store": false }
```
**Response `201`**
```json
{ "assessment_id": "834d8e31…", "created_at": "2026-09-29T17:49:22+00:00",
  "overall_score": 82, "risk_level": "CRITICAL",
  "category_scores": { "profile_exposure": 100, "personal_information": 78, "...": 0 },
  "category_levels": { "profile_exposure": "CRITICAL", "...": "..." },
  "high_risk_categories": ["profile_exposure", "tagging_risk", "..."],
  "findings": [ { "finding_type": "phone_public", "category": "personal_information",
                  "severity": "HIGH", "title": "Phone number reported as publicly visible", "...": "..." } ],
  "top_findings": ["first 5 findings"],
  "recommendations": [ { "finding_type": "phone_public", "priority": "IMMEDIATE",
                         "recommendation": "Limit phone-number visibility…", "why": "…" } ],
  "security_controls": { "enabled_count": 0, "total": 10, "controls": ["…"] },
  "stored": false, "disclaimer": "This is an educational privacy-risk framework…" }
```
When `store` is `true`, the response also contains a one-time `delete_token`.

### POST /api/assessment/simulate-improvement
```json
{ "responses": { "...all 53..." }, "changes": { "mfa_enabled": "YES" }, "fix_findings": ["phone_public"] }
```
`fix_findings` may also be `"ALL"`. The response includes `current`, `simulated`, `risk_reduction`, `changes_applied`, `category_changes` and a `disclaimer`.

### DELETE /api/assessment/{id}
Header `X-Delete-Token: <token from creation>` → `200 {"deleted": true}`. A missing token returns `401`. A wrong token or unknown id returns the same `404`, so ids can't be probed.

### Cross-cutting behaviour

| Concern | Implementation |
|---|---|
| **Validation** | JSON object required; unknown question ids rejected; answers must be an allowed code; all 53 required (partial allowed only for `changes`); id format `^[0-9a-f]{32}$`; body ≤ 16 KB. |
| **Error handling** | `400 {"error": "Validation failed.", "details": [...]}` · `401` · `404` · `405` · `413` · `429` with `Retry-After` · `500` with a generic message (stack traces are only logged server-side). |
| **Authentication** | None by design: the app has **no user accounts**, which avoids collecting identity data at all. |
| **Authorization** | Capability model: a saved result is readable only by someone holding its random 128-bit id, and deletable only with its secret deletion token (stored hashed). |
| **Rate limiting** | POST and DELETE endpoints: 30 requests/minute per client (configurable). |
| **Privacy** | No raw answers stored; no IP logging to disk; `Cache-Control: no-store`; `Referrer-Policy: no-referrer` so ids don't leak through the Referer header. |
