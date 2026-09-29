# Project Report: Social Media Privacy Risk Assessment Framework

> Covers brief section 43 (and 45, Future Improvements, under *Future Scope*). Written for course submission. Fill in the roll number and institution before submitting.

**Title:** Social Media Privacy Risk Assessment Framework
**Author:** Nischay Prasad · [Roll Number] · [Course / Institution]
**Date:** September 2026

---

## Abstract
Social-media users often protect their accounts with passwords while still exposing personal information that enables profiling, impersonation and social engineering. This project presents a defensive, educational framework that estimates social-media privacy risk from **self-reported** settings and habits, without collecting any personal data. A 53-question questionnaire across ten categories is converted into numerical risk features, scored per category, and combined into a 0–100 Privacy Risk Score through configurable weights, then classified as Low, Moderate, High or Critical. A findings engine ranks weaknesses by severity, a recommendation engine produces prioritised remediation, and an improvement simulator quantifies the effect of proposed changes. The system is implemented in Python (Flask) with SQLite and a JavaScript/Chart.js frontend, follows privacy-by-design principles (data minimisation, privacy by default, retention limitation, user deletion), and is validated by 65 automated tests. A 1,000-record synthetic dataset supports aggregate analytics. On a fictional over-sharing profile the framework reports 82/100 (Critical). Applying eleven recommended changes lowers it to 53 (High), and applying all recommendations lowers it to 2 (Low).

## 1. Introduction
Social platforms encourage sharing, and their audience, tagging, location and integration settings are numerous and change over time. Most users never audit them systematically. Security teams and awareness programmes need a structured, explainable way to show individuals where their exposure comes from and what to fix first. This project provides that structure while practising what it preaches: it assesses privacy without invading it.

## 2. Problem Statement
Individuals lack a simple, private way to:
1. understand how exposed they are across the many dimensions of social-media privacy,
2. distinguish **privacy** exposure from **account-security** weaknesses,
3. prioritise which changes matter most, and
4. see the measurable benefit of those changes.

Existing tools either inspect real profiles, which raises privacy and ethical concerns, or give generic advice with no prioritisation.

## 3. Objectives
- Design a questionnaire of at least 40 questions across ten privacy/security categories that never collects sensitive values.
- Build a transparent feature-extraction and weighted scoring model (category scores, overall score, four risk levels).
- Generate ranked findings and personalised, prioritised recommendations.
- Provide a what-if improvement simulator.
- Provide a dashboard, a printable report and a checklist.
- Apply privacy by design and secure-coding practices in the application itself.
- Validate the system with automated functional, security and privacy tests.
- Use only synthetic or voluntarily self-reported data.

## 4. Social Media Privacy Background
Social-media privacy concerns which personal attributes are exposed, to which audiences, and for how long. Individually low-risk attributes (city, employer, school, birthday) combine into high-risk profiles (*aggregation*). Exposure also comes from others (tags, group photos) and from third-party applications granted access to profile data.

## 5. Digital Footprint
The active footprint is deliberately shared content; the passive footprint is data generated through activity, depending on the service. Historical posts, forgotten accounts and public comments persist and are often indexed. The framework evaluates only self-reported footprint *practices* (reviewing old posts, removing old accounts, periodic settings reviews) and does not measure any real footprint.

## 6. Privacy vs Security
Privacy governs how personal information is collected, shared and used. Security protects accounts and systems from unauthorised access. They overlap, since a compromised account exposes private content and exposed data enables targeted attacks, but they are not identical: an account with MFA can still publish its owner's live location. The framework therefore scores Account Security as its own category alongside nine exposure-oriented categories.

## 7. Social Engineering
Social engineering manipulates trust, urgency and authority. Public personal context makes pretexts more believable. The framework assesses defensive behaviours (link checking, refusing to share verification codes, out-of-band verification, caution with giveaways and DMs) and provides awareness material. No attack content is included.

## 8. Existing Approaches
| Approach | Strength | Limitation |
|---|---|---|
| Platform "privacy checkup" wizards | Built into the platform | Platform-specific; no cross-category risk score; no prioritisation across services |
| Generic awareness checklists | Simple | Not personalised; no measurement |
| OSINT / profile-scanning tools | Measure real exposure | Require inspecting real profiles, which raises privacy, consent and misuse concerns |
| Enterprise security-awareness platforms | Organisation-wide | Commercial; often focused on phishing simulation rather than personal privacy configuration |

This framework takes the self-assessment route: it's personalised, measurable and prioritised, and it's non-invasive by design.

## 9. Proposed Framework
Questionnaire → validation → feature extraction → ten category analyses → weighted overall score → classification → findings → recommendations → simulator, dashboard and report. Every component reads a single questionnaire definition, so the model is consistent and auditable.

## 10. Architecture
A Flask application serves a REST API and a static frontend from one origin. Business logic lives in pure-Python service modules that are independent of Flask and the database. A thin data-access layer persists only minimised results in SQLite when the user opts in. See `docs/04_ARCHITECTURE_API_DATABASE.md` for diagrams, the schema and the API specification.

## 11. Questionnaire Design
53 questions in ten categories (A–J). Answers use fixed scales: exposure (Yes/Sometimes/No/Not sure), protective control (inverse), visibility (Public/Friends/Private), frequency (Always/Often/Sometimes/Never) and recency. "Not sure" is scored as moderate risk, since an unconfirmed protection can't be relied on. Each question has a weight (1.0–3.0) and an impact rating (High/Medium/Low). Full list: `docs/02_PRIVACY_QUESTIONNAIRE.md`.

## 12. Synthetic Dataset
1,000 fictional records are generated from four personas (privacy-conscious, average, casual sharer, oversharer) with per-category variation, and every record is scored by the production engine. Generation is seeded and reproducible. Resulting distribution: Low 151, Moderate 244, High 395, Critical 210; mean score 47.9.

## 13. Feature Engineering
`extract_privacy_features()` maps each validated answer to a risk value in [0, 1] via its scale, producing a flat feature vector and a per-category grouping.

## 14. Category Risk Analysis
Category score = 100 × Σ(wᵢ·rᵢ) / Σwᵢ over the category's questions. The ten analyses cover profile visibility, personal information, location, content, connections, tagging, account security, third-party apps, social engineering and digital footprint.

## 15. Risk Scoring
Overall score = weighted average of category scores (default weights 10/15/15/10/10/5/15/5/10/5). Levels: 0–20 Low, 21–40 Moderate, 41–70 High, 71–100 Critical. Weights and thresholds are configurable and explicitly documented as **educational assumptions** requiring validation before professional use.

## 16. Findings Engine
Answers with risk ≥ 0.5 become findings. Severity combines the question's impact with the answer's risk value. Findings are ranked by severity, then by risk × question weight × category weight.

## 17. Recommendation Engine
A catalog maps each finding type to a defensive recommendation and rationale. Priority follows severity (High → Immediate, Medium → Important, Low → Good practice). Direct account-takeover paths (no MFA, password reuse, sharing codes) are always Immediate.

## 18. Improvement Simulator
Applies explicit answer changes, or sets selected findings to their safest answers, then re-runs the same engine and reports before/after and per-category deltas. It stores nothing and is labelled as a framework simulation, not a guarantee.

## 19. Account Security
MFA, password reuse, password manager, login alerts, recovery information and session review. These form the ten security controls shown on the results page (together with tag review, follower approval, connected-app review and settings review).

## 20. Third-Party Applications
Connected-app review, unused integrations, social login and quiz-app permissions, analysed against the principle of least privilege.

## 21. Location Privacy
Public city, live location, geotags, real-time check-ins, travel posts and routine patterns. The recommendation of "late posting" reduces immediate exposure. The application performs no geolocation.

## 22. Digital Footprint Analysis
Self-reported practices: old-post review, old accounts, public comments, settings-review recency, username reuse and self-search.

## 23. Privacy Dashboard
Shows the user's latest result (from browser session storage) beside synthetic-population aggregates: category comparison, risk distribution, top weaknesses, control adoption, digital-footprint distribution and before/after simulation.

## 24. Privacy by Design
Data minimisation, purpose limitation, least privilege, privacy by default, transparency, user control, retention limitation and secure processing, each mapped to code and tests in `docs/08_PRIVACY_BY_DESIGN.md`.

## 25. Testing
65 automated pytest tests, including the 30 specified scenarios (TC01–TC30): single-weakness isolation from a fully private baseline, calculation checks against hand-computed values, boundary tests at 20/21, 40/41 and 70/71, recommendation ordering, simulation, persistence and report generation. See `docs/05_TESTING.md`.

## 26. Security Testing
Tests verify that the schema contains only approved non-sensitive columns and that a full database dump holds no raw answers or plaintext tokens. They also cover input allow-listing, oversize rejection, XSS escaping, security headers, rate limiting (201, 201, 201, 429), generic errors, token-protected deletion, retention purging and environment-based configuration.

## 27. Results
- **Demo profile (fictional over-sharer):** 82/100 Critical; 48 findings; 9 of 10 categories High or Critical; 0 of 10 security controls on.
- **Improvement simulation:** 11 changes from the brief → 53/100 High (−29 points). All recommendations → 2/100 Low.
- **Top-5 simulation in the UI:** fixing only the five highest-ranked findings → 68/100 (−14).
- **Synthetic population (n = 1,000):** mean 47.9. The most common weaknesses were login alerts off (58.2%), MFA off (57.3%) and tag review off (55.2%). The least-adopted controls were connected-app review (22.5%) and old-post review (25.7%).
- **Quality:** 65/65 tests passing; no horizontal scroll at 375 px; light and dark themes.

Because the dataset is synthetic, these population figures show that the pipeline works, not real-world prevalence.

## 28. Limitations
- **Self-reported input:** users may misjudge or misremember their settings.
- **Uncalibrated weights:** weights, thresholds and impact ratings are expert-style assumptions, not fitted to incident data.
- **Linear model:** doesn't capture interactions between exposures (aggregation effects).
- **Platform-agnostic:** doesn't reflect platform-specific settings names or defaults.
- **Synthetic analytics:** dashboard aggregates don't represent real populations.
- **Single-process rate limiting** and a development server: not production-hardened.
- Chart.js and fonts load from CDNs (SRI-pinned), which adds third-party requests.

## 29. Future Scope (brief section 45)
All improvements remain defensive. No scraping or monitoring will be added.
- **Platform-specific privacy checklists** with step-by-step setting locations.
- **Configurable organisational policies:** custom weights, thresholds and required controls per organisation.
- **Privacy-awareness quizzes** and a **privacy maturity score** (initial → optimised).
- **Family / teen safety education modules** with age-appropriate guidance.
- **Enterprise employee privacy training** with anonymous organisational trend analysis (k-anonymity thresholds before showing any group).
- **GRC reporting:** exportable control matrices and trends over time.
- **Better risk-model calibration:** expert elicitation, sensitivity analysis and interaction terms.
- **Localisation** and **accessibility** audits (WCAG 2.2 AA).
- **Report comparison over time** (client-side, user-held).
- **Secure client-side assessment / optional local-only mode:** run the engine entirely in the browser (e.g. via Pyodide or a JavaScript port) so answers never leave the device.

## 30. Conclusion
The framework shows that privacy risk can be assessed in a structured, explainable and actionable way without collecting personal data. By separating exposure from account security, ranking findings and quantifying improvements, it turns general advice into a personal plan. Building the application under privacy-by-design and secure-coding constraints, and proving those constraints with tests, gave practical experience of the controls that security and privacy professionals are expected to design, assess and explain.

## References
1. NIST Privacy Framework v1.0 (2020).
2. NIST SP 800-63B, Digital Identity Guidelines: Authentication and Lifecycle Management.
3. OWASP Top 10 (2021) and OWASP Cheat Sheet Series (XSS Prevention, Content Security Policy, Input Validation).
4. Cavoukian, A., *Privacy by Design: The 7 Foundational Principles*.
5. EU General Data Protection Regulation (GDPR), Article 5 (principles) and Article 25 (data protection by design and by default).
6. CISA, "Avoiding Social Engineering and Phishing Attacks" (Security Tip ST04-014).
