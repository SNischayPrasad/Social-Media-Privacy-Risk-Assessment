# 9. GitHub Upload, Screenshot Proof and Resume / LinkedIn

> Covers brief sections 40 (GitHub Upload Strategy), 42 (Screenshot / Proof Checklist) and 44 (Resume / LinkedIn Proof).

## 40. GitHub Upload Strategy

**Repository name:** `Social-Media-Privacy-Risk-Assessment`

**Description:**
> Privacy-focused cybersecurity framework for assessing social-media exposure, account-security practices, social-engineering risk, digital-footprint risk, and personalized privacy improvements using synthetic/self-reported data.

**Topics:** `cybersecurity` `privacy` `social-media-privacy` `privacy-risk` `security-awareness` `python` `flask` `digital-footprint` `risk-assessment` `grc` `privacy-by-design` `defensive-security`
(Add `fastapi` only if you complete the FastAPI port; topics should describe what's actually in the repo.)

### Before the first push
1. Run the tests: `python -m pytest`, and confirm 65 pass.
2. Confirm `.env`, `venv/` and `instance/` are **not** staged: `git status` must not list them (they're in `.gitignore`).
3. Add your screenshots to `screenshots/`.
4. Check the Author section in `README.md` (add your LinkedIn URL).

### Option 1: one initial commit (fastest)
Create an **empty** repository on GitHub (no README or licence), then from the project folder:

```bash
git init
git add .
git commit -m "Initialize social media privacy risk assessment"
git branch -M main
git remote add origin https://github.com/SNischayPrasad/Social-Media-Privacy-Risk-Assessment.git
git push -u origin main
```

### Option 2: a meaningful commit history (recommended for your portfolio)
Commit the project in logical steps. Each block below stages the files for that step:

```bash
git init
git add .gitignore requirements.txt .env.example run.py backend/__init__.py backend/app.py backend/config.py backend/routes/__init__.py backend/models/__init__.py backend/services/__init__.py backend/utils/__init__.py
git commit -m "Create privacy assessment architecture"

git add backend/services/questionnaire.py backend/utils/validators.py tools/export_questionnaire.py docs/02_PRIVACY_QUESTIONNAIRE.md
git commit -m "Add privacy questionnaire"

git add backend/services/demo_profiles.py data/
git commit -m "Generate synthetic assessment dataset"

git add backend/services/assessment_engine.py
git commit -m "Implement privacy feature extraction"

git add backend/services/scoring_engine.py
git commit -m "Add category risk scoring"
```

Some of these steps only become runnable once later files exist. That's fine for history purposes. If you'd rather each commit run, combine *feature extraction* and *scoring* into one commit. Continue:

```bash
git add backend/services/findings_engine.py
git commit -m "Add privacy findings engine"

git add backend/services/recommendation_engine.py backend/services/checklist.py
git commit -m "Implement recommendation engine"

git add backend/services/improvement_simulator.py tools/run_demo.py
git commit -m "Build privacy improvement simulator"

git add backend/services/dashboard_service.py backend/routes/ frontend/
git commit -m "Create privacy analytics dashboard"

git add backend/services/report_generator.py reports/
git commit -m "Add privacy assessment report"

git add backend/models/database.py backend/utils/security.py tools/photo_metadata_viewer.py
git commit -m "Implement privacy-by-design controls"

git add tests/
git commit -m "Add automated privacy tests"

git add README.md docs/ screenshots/
git commit -m "Complete README and documentation"

git add -A
git status          # should show nothing left, or only files you intend to add
git branch -M main
git remote add origin https://github.com/SNischayPrasad/Social-Media-Privacy-Risk-Assessment.git
git push -u origin main
```

**Tip:** if you keep developing, make small commits with messages that say *what changed and why*, for example "Treat NOT_SURE as moderate risk in protective controls".

---

## 42. Screenshot / Proof Checklist

Save screenshots in `screenshots/` with these names. The README already links several of them.

| # | What to capture | Filename |
|---|---|---|
| 1 | Project folder structure (VS Code explorer) | `01_project_structure.png` |
| 2 | Architecture diagram (README or docs/04) | `02_architecture_diagram.png` |
| 3 | Overview / homepage | `03_homepage.png` |
| 4 | Questionnaire (first category) | `04_questionnaire.png` |
| 5 | Profile privacy section (Category A) | `05_profile_privacy_section.png` |
| 6 | Personal-information section (Category B) | `06_personal_information_section.png` |
| 7 | Location section (Category C) | `07_location_section.png` |
| 8 | Account-security section (Category G) | `08_account_security_section.png` |
| 9 | Social-engineering section (Category I) | `09_social_engineering_section.png` |
| 10 | Overall risk score panel | `10_overall_risk_score.png` |
| 11 | Stats row / category scores | `11_category_scores.png` |
| 12 | Category risk chart | `12_privacy_risk_chart.png` |
| 13 | Top findings | `13_top_findings.png` |
| 14 | Recommendations | `14_recommendations.png` |
| 15 | Simulator before running | `15_simulator_before.png` |
| 16 | Simulator after running | `16_simulator_after.png` |
| 17 | Risk reduction and before/after chart | `17_risk_reduction.png` |
| 18 | Dashboard top | `18_privacy_dashboard.png` |
| 19 | Risk distribution chart | `19_risk_distribution.png` |
| 20 | Top weaknesses chart | `20_top_weaknesses_chart.png` |
| 21 | Privacy checklist | `21_privacy_checklist.png` |
| 22 | Privacy report (HTML/PDF) | `22_privacy_report.png` |
| 23 | Synthetic dataset (CSV opened in Excel) | `23_synthetic_dataset.png` |
| 24 | `pytest -v` output (65 passed) | `24_automated_tests.png` |
| 25 | Security/privacy tests output | `25_security_privacy_tests.png` |
| 26 | Database schema (DB Browser for SQLite, or docs/04) | `26_database_schema.png` |
| 27 | GitHub commit history | `27_github_commits.png` |
| 28 | GitHub repository page | `28_github_repository.png` |
| 29 | README preview on GitHub | `29_readme_preview.png` |

**Quick way to reach each state:** open `assessment.html` → **Use fictional demo answers** → click categories A, B, C, G and I in the sidebar for screenshots 5–9 → **Calculate my privacy score** → scroll for 10–17 → Dashboard for 18–20.

For 25: `python -m pytest tests/test_security_privacy.py -v`.

---

## 44. Resume / LinkedIn Proof

### A. Resume bullet points
- Built a **privacy-by-design risk assessment framework** (Python, Flask, SQLite) that scores social-media exposure across 10 weighted categories from a 53-question self-assessment, producing ranked findings, prioritised recommendations and printable reports **without collecting any personal data**.
- Implemented **application-security controls**, including allow-list input validation, CSP and security headers, rate limiting, parameterised SQL, HTML output encoding, hashed deletion tokens and a 30-day retention policy. Verified them with **65 automated pytest tests**, including tests proving no PII or raw answers are stored.
- Generated a **1,000-record synthetic dataset** scored by the production engine and built an analytics dashboard (Chart.js) plus a **what-if improvement simulator**. The simulator showed that 11 setting changes cut a demo profile's risk from 82 (Critical) to 53 (High).

### B. Two-line project description
A defensive cybersecurity project that estimates social-media privacy risk from self-reported settings and turns it into personalised, prioritised fixes. It's built on privacy-by-design principles: no scraping, no personal data, and synthetic data for analytics.

### C. LinkedIn project description
> **Social Media Privacy Risk Assessment Framework** · Python · Flask · SQLite · Chart.js
>
> Many people with strong passwords still publish their birthday, workplace and live location. I built a framework that measures that gap between *security* and *privacy*.
>
> Users answer 53 questions about their own settings. The engine converts each answer into a risk feature, scores 10 categories (profile visibility, personal information, location, content, connections, tagging, account security, third-party apps, social engineering, digital footprint) and combines them into a 0–100 score with Low/Moderate/High/Critical levels. It then produces ranked findings, prioritised recommendations, a printable report, and a simulator that shows how much specific changes would reduce risk.
>
> The app follows privacy by design. It asks *whether* data is visible, never for the data itself, stores nothing by default, and stores only scores if you opt in, with deletion and retention controls. It's secured with input allow-listing, CSP, rate limiting and output encoding, and tested with 65 automated tests. The analytics use a 1,000-record synthetic dataset, and no real users are profiled.
>
> Skills: privacy risk assessment · threat modelling · risk scoring · GRC concepts · secure coding · Python · data analytics · security awareness

### D. Technical skills demonstrated
| Area | Skills |
|---|---|
| Cybersecurity | Threat modelling, risk matrices, control assessment, account-takeover defences (MFA, password hygiene, session review) |
| Privacy | Privacy risk assessment, PII exposure analysis, data minimisation, privacy by design/default, retention, digital-footprint analysis |
| AppSec | Input validation, XSS prevention, CSP, SQL-injection prevention, rate limiting, secure error handling, SRI |
| GRC | Weighted control frameworks, documented assumptions, likelihood/impact ratings, audit-friendly reporting |
| Security awareness | Social-engineering awareness, personalised guidance, checklists |
| Engineering | Python, Flask, REST API design, SQLite schema design, JavaScript, Chart.js, pytest |
| Data | Synthetic data generation, aggregation, visualisation |

### E. GitHub repository description
> Privacy-focused cybersecurity framework for assessing social-media exposure, account-security practices, social-engineering risk, digital-footprint risk, and personalized privacy improvements using synthetic/self-reported data.
