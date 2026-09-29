# 8. Privacy by Design: How This Application Follows It

> Covers brief section 39. Each principle is linked to the code that implements it and, where possible, to a test that proves it.

| Principle | Meaning | How this application applies it | Evidence |
|---|---|---|---|
| **Data Minimisation** | Collect only what is needed for the purpose | Questions ask *whether* data is visible, never the data itself. Only fixed answer codes are accepted. Raw answers are scored and discarded. The DB stores only scores and finding types. | `utils/validators.py`, `models/database.py`; tests TC29, `test_validation_rejects_unknown_questions_and_free_text` |
| **Purpose Limitation** | Use data only for the stated purpose | Saved results are used only for the user's own report and anonymous aggregate counts. There's no analytics SDK, tracking, advertising or sharing. | `dashboard_service.py` returns aggregates only |
| **Least Privilege** | Give components only the access they need | Routes can't run SQL directly (only through `Database`); the report has no script capability (`default-src 'none'`); `Permissions-Policy` denies camera, microphone and geolocation; the server binds to `127.0.0.1` by default | `utils/security.py`, `config.py` |
| **Privacy by Default** | The most private option is the default | Saving is **off** by default (`"store": false`; checkbox unticked). Answers stay in `sessionStorage`, which is cleared when the tab closes. | `test_assessment_not_stored_by_default` |
| **Transparency** | Tell users what happens to their data | The overview page lists what's never collected; the consent text explains exactly what's saved and for how long; the scoring model and weights are documented; results carry a disclaimer | `index.html`, `assessment.html`, `docs/03_…` |
| **User Control** | Users can see, export and delete their data | A one-time deletion token is issued; `DELETE /api/assessment/{id}`; a "Clear my answers" button; the report can be downloaded | `test_stored_data_can_be_deleted` |
| **Retention Limitation** | Don't keep data longer than necessary | Saved results older than `RETENTION_DAYS` (default 30) are purged at start-up | `test_retention_policy_purges_old_assessments` |
| **Secure Processing** | Protect data while it's processed and stored | Allow-list validation, parameterised SQL, HTML escaping, CSP and security headers, rate limiting, body-size limit, hashed deletion tokens, generic error messages, SRI-pinned CDN script | `test_security_privacy.py` |

### Why not store raw answers "just in case"?
Answers describe a person's security weaknesses (for example "no MFA, password reused"). Stored alongside an identifier, that becomes a target list. Storing only aggregate scores keeps the useful part (a trend dashboard) and removes the dangerous part. **Data you never collect can never be breached.**

### What would change for a production deployment
- HTTPS everywhere, plus HSTS.
- A shared rate-limit store (Redis) or a gateway/WAF.
- A production WSGI server (gunicorn/waitress) instead of the Flask dev server.
- A formal privacy notice and a Data Protection Impact Assessment (DPIA).
- Self-hosting Chart.js and fonts, removing third-party requests entirely.
