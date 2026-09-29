# 6. Threat Model and Privacy Risk Matrix

> Covers brief sections 35 (Threat Model) and 36 (Privacy Risk Matrix). The analysis is defensive: it identifies what to protect and which controls reduce risk. It contains no attack instructions.

**Subject:** a *fictional* social-media user ("Demo Riya", the demo profile). Their answers are the input to the model.

## 35. Threat Model

### Assets
| Asset | Description |
|---|---|
| Account | Login access to the social-media account |
| Identity information | Name, photo, birth date, education, workplace |
| Contact information | Phone number, personal email |
| Location privacy | Home area, real-time location, routines, travel |
| Private content | Friends-only posts, messages, photos |
| Social relationships | Friends/followers list, family members |

### Threats, exposures and controls

| Asset | Threat | Exposure (what makes it possible) | Potential Impact | Existing Control (typical) | Recommended Control |
|---|---|---|---|---|---|
| Account | **Account takeover** | No MFA; password reused on other sites; recovery info outdated | Loss of account, private content exposed, impersonation of the user to friends | Password only | Enable MFA (app or security key); unique password with a password manager; review recovery options and active sessions; login alerts |
| Identity information | **Impersonation** (clone accounts) | Public profile photo, name, friends list, bio | Friends and family targeted by a fake account; reputational harm | Platform reporting tools | Limit friends-list visibility; restrict profile photo and sections; tell contacts to verify unusual requests through another channel |
| Contact information | **Phishing** (email / SMS / DM) | Public phone and email; discoverable by contact info | Credential theft, malware, fraud | Spam filters | Hide phone and email; disable lookup by phone/email; check links before opening; use the official app instead of links |
| Account + identity | **Social engineering / pretexting** | Public employer, school, travel, family details make pretexts believable; accepting unknown connections | Disclosure of codes or information; money requested by "friends" | User judgement | Verify unknown profiles; never share verification codes; verify urgent requests out of band; reduce public context |
| Location privacy | **Unwanted profiling / physical-safety risk** | Real-time location, geotags, check-ins, travel posts, routines | Stalking or harassment risk; home known to be empty | Audience selector | Turn off live location for broad audiences; post after leaving; share travel after returning; avoid routine patterns; review photo backgrounds and metadata |
| All personal data | **Oversharing / aggregation** | Public posts by default; old posts never reviewed; same username everywhere | A detailed profile assembled from many small pieces | None | Default audience to friends; periodic review of old posts; different usernames; self-search |
| Private content + relationships | **Third-party application exposure** | Old quiz apps and unused integrations with broad permissions; frequent social login | Data held and possibly misused outside the platform | Platform app review | Review and revoke apps (least privilege); prefer separate accounts over social login |
| Identity + location | **Exposure via others (tagging)** | Anyone can tag; no tag review; tagged posts auto-visible | Being placed at locations or events without consent | None | Enable tag review; restrict who can tag or mention; remove unwanted tags |

### Trust boundaries in *this application*
| Boundary | Threat | Control in the code |
|---|---|---|
| Browser → API | Malicious or oversized input, XSS payloads | Allow-list validation, 16 KB body limit, rate limiting, `textContent` rendering, CSP |
| API → Database | SQL injection, over-collection | Parameterised SQL; schema without PII columns; opt-in storage |
| Database at rest | Data breach of stored results | Only scores and finding types stored; hashed deletion tokens; 30-day retention |
| Report output | Script injection via report | HTML escaping; no scripts; `default-src 'none'` CSP |

## 36. Privacy Risk Matrix

**Likelihood:** how often this exposure is realistically abused. **Impact:** how bad the outcome is if it is.

| Exposure | Likelihood | Impact | Rating |
|---|---|---|---|
| Public phone number | Medium | Medium | **Medium** |
| Public personal email | Medium | Medium | **Medium** |
| Full birth date public | Medium | Medium | **Medium** |
| Home address / neighbourhood public | Low | High | **Medium–High** |
| Real-time location exposure | Medium | High | **High** |
| Travel plans posted in advance | Medium | High | **High** |
| MFA disabled | Medium | High | **High** |
| Password reuse | High | High | **Critical** |
| Sharing verification codes | Medium | High | **High** |
| Accepting unknown connections | High | Medium | **High** |
| Tag review disabled | Medium | Low | **Low–Medium** |
| Third-party apps never reviewed | Medium | Medium | **Medium** |
| Old public posts never reviewed | Medium | Low | **Low–Medium** |
| Public education details | Low | Low | **Low** |

```
              IMPACT →   LOW                 MEDIUM                          HIGH
LIKELIHOOD
HIGH                     ·                   Unknown connections             Password reuse
MEDIUM                   Tag review off,     Phone, email, birthday,         Real-time location, travel plans,
                         old posts           third-party apps                MFA disabled, sharing codes
LOW                      Education           ·                               Home address public
```

> **Actual risk depends on context.** A public figure, a person facing harassment, a teenager and a small-business owner face very different likelihoods and impacts for the same setting. The questionnaire's `impact` field and category weights encode one reasonable default. In a professional setting they would be tailored to the population being assessed.
