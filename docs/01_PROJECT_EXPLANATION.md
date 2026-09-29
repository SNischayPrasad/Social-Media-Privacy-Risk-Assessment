# 1. Project Explanation, Industry Relevance, Privacy vs Security

> Covers brief sections 1 (Project Explanation), 2 (Industry Relevance) and 3 (Privacy vs Security).

This project is a **defensive, educational privacy-risk framework**. A user answers questions about *their own* social-media settings and habits, and the framework estimates how exposed they are. It never looks at a real profile, never scrapes, and never asks for the sensitive value itself. It asks "Is your phone number public?", never "What is your phone number?".

> **Important:** The score is an educational estimate built from self-reported answers and teaching assumptions. It does not guarantee that an account will or will not be compromised.

---

## 1.1 Key concepts

### Social-media privacy
**Simple:** Deciding who can see what you share, and how much of your life a stranger can piece together from your profile.
**Technical:** The set of platform controls (audience settings, discoverability, tagging, integrations) and user behaviours that determine which personal data elements are exposed, to which audiences, and for how long.

### Digital footprint
**Simple:** The trail you leave online.
**Technical:** The *active* footprint is what you deliberately publish (posts, bio, comments). The *passive* footprint is data generated about you through activity (logs, tags by others, metadata, third-party app data), depending on the service. This project evaluates only **self-reported** practices; it does not measure anyone's actual footprint.

### Personal-information exposure
**Simple:** Details like your phone, birthday or workplace being visible to people who don't need them.
**Technical:** The number and sensitivity of identifying attributes (PII / quasi-identifiers) that are readable by an audience. Individually harmless attributes such as city, employer and birth date can combine to re-identify or profile someone. This is called *aggregation risk*.

### Oversharing
**Simple:** Posting more than you realise, such as where you are right now, when your home is empty, or what's on your screen.
**Technical:** Publishing content whose informational value to an adversary exceeds its social value to you. This includes real-time location, travel plans, routines, and background details in photos (badges, documents, plates).

### Social engineering
**Simple:** Tricking people instead of hacking computers, for example with a message that seems to come from a friend or a company.
**Technical:** Manipulation techniques (pretexting, phishing, impersonation, baiting) that exploit trust, urgency or authority. Publicly available personal context makes pretexts more believable. This project only *raises awareness*; it contains no attack content.

### Identity-related risk
**Simple:** Someone pretending to be you, or using your details to get into your accounts.
**Technical:** Risks such as impersonation, account takeover via weak recovery options or knowledge-based questions, and fraud that uses exposed attributes (birth date, family names, phone number).

### Why location exposure creates privacy risk
Real-time location shows where you are *now*, and by implication where you are *not* (for example, your home). Repeated geotags reveal routines. Travel plans posted in advance announce absences. **Posting after you leave** a place reduces immediate exposure compared with broadcasting it live, although the history still adds to your footprint.

### Why public profiles increase exposure
Public is not automatically unsafe; creators and professionals often need it. But a public profile removes the audience filter, so everything on it is available to anyone, including automated collection and people building a profile of you. Visibility multiplies the impact of every other disclosure.

### Why historical posts matter
Years of posts form a timeline: schools, workplaces, friends, addresses, habits. Old content is rarely reviewed, may predate current privacy settings, and can be indexed by search engines.

### Why privacy settings should be reviewed regularly
Platforms add features, change defaults and rename settings. Life changes too: new job, new city, new relationships. A setting that was right three years ago may not be right now.

### How MFA helps account security
Multi-factor authentication requires something besides the password (an authenticator app, security key or SMS code). A stolen, guessed or reused password alone is then usually not enough to log in. Phishing-resistant methods (security keys / passkeys) are strongest. MFA does **not** reduce what your profile exposes; that's a privacy question.

### Privacy vs security (short version)
Privacy decides **what is exposed and to whom**. Security decides **who can get in and change things**. Section 3 expands on this.

---

## 1.2 Workflow

```
User
 ↓
Privacy Questionnaire ........ 53 questions, fixed answer codes (frontend/assessment.html)
 ↓
Input Validation ............. allow-list of question ids and answer codes (backend/utils/validators.py)
 ↓
Privacy Feature Extraction ... each answer -> risk value 0.0-1.0 (assessment_engine.extract_privacy_features)
 ↓
Category Risk Analysis ....... weighted score 0-100 for each of 10 categories (scoring_engine.calculate_category_scores)
 ↓
Risk Scoring Engine .......... weighted average with configurable weights (scoring_engine.calculate_privacy_risk)
 ↓
Overall Privacy Risk Score ... 0-100 (higher = more exposure)
 ↓
Risk Classification .......... LOW 0-20 | MODERATE 21-40 | HIGH 41-70 | CRITICAL 71-100
 ↓
Personalized Recommendations . findings_engine + recommendation_engine
 ↓
Privacy Dashboard ............ frontend/dashboard.html + GET /api/dashboard/stats
 ↓
Privacy Assessment Report .... report_generator.render_report_html (HTML -> Print to PDF)
```

---

## 2. Industry Relevance

| Area | How this project relates |
|---|---|
| **Cybersecurity** | Models attack surface created by exposed personal data; covers account-takeover controls (MFA, password reuse, login alerts, sessions). |
| **Privacy engineering** | Implements data minimisation, purpose limitation, privacy by default, retention limits and user deletion in real code. |
| **Security awareness** | Turns abstract advice into personalised, prioritised actions and a printable checklist. |
| **Enterprise security** | Employees' public profiles feed spear-phishing and pretexting; aggregated (anonymous) results can guide awareness training. |
| **Digital-risk management** | Quantifies exposure categories with a transparent, configurable scoring model. |
| **Identity protection** | Flags attributes commonly used in identity verification (birth date, phone, family names, recovery info). |
| **Security consulting** | Mirrors a consultant's workflow: questionnaire → findings → risk rating → prioritised remediation → report. |
| **Application security** | The app itself uses input allow-listing, output encoding, CSP, rate limiting, parameterised SQL and safe error handling. |
| **Governance, Risk & Compliance** | Uses a likelihood/impact risk matrix, a threat model, weighted control assessment and documented assumptions. |
| **Employee cybersecurity training** | The simulator ("what if I fix these?") shows the effect of behaviour change, which motivates people. |

### Relevant job roles and what this project demonstrates

| Role | Skills demonstrated |
|---|---|
| **Cybersecurity Analyst** | Threat modelling, control assessment, risk scoring, security testing |
| **Privacy Analyst** | PII exposure analysis, data minimisation, privacy-by-design controls, retention |
| **GRC Analyst** | Risk matrix, weighted control frameworks, documented assumptions, reporting |
| **SOC Analyst** | Understanding phishing/social-engineering signals, account-compromise indicators (login alerts, sessions) |
| **Security Consultant** | Assessment → findings → prioritised recommendations → client-ready report |
| **IAM Analyst** | MFA, password reuse, recovery options, session management, third-party (OAuth) app access, least privilege |
| **Security Awareness Specialist** | Personalised guidance, checklist, social-engineering awareness content |
| **Privacy Engineer** | Building the privacy controls into the application: schema design, no raw-answer storage, deletion tokens, CSP |

---

## 3. Privacy vs Security

**PRIVACY** controls how personal information is collected, shared, exposed and used.
**SECURITY** protects systems, accounts and information from unauthorised access or misuse.

> **Strong account security ≠ strong privacy.**

| Example | Security | Privacy | What's wrong |
|---|---|---|---|
| MFA on, unique password, but full birth date, workplace and live location public | Strong | Weak | Nobody can log in as you, but anyone can profile you and build a convincing scam. |
| Fully private profile, but password reused from a breached site and no MFA | Weak | Strong | Little is visible, but an attacker can log in and see everything. |
| Private profile, MFA on, but an old quiz app still has full profile access | Mixed | Weak | A third party holds your data outside your privacy settings. |
| Tag review off, friends post geotagged photos of you | n/a | Weak | Other people's posts expose you even if you post nothing. |
| You share an OTP code with a "support agent" | Broken | n/a | MFA is bypassed by social engineering, so security relies on behaviour too. |

The framework scores both sides separately (the *Account Security* category versus the exposure categories), so a user can see that fixing one does not fix the other.
