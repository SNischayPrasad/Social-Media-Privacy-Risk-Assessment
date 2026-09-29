# Privacy Assessment Questionnaire

> Auto-generated from `backend/services/questionnaire.py` by `tools/export_questionnaire.py`.

**53 questions in 10 categories.** No question asks for the sensitive value itself (for example, the phone number). Each question asks only whether something is visible or enabled.

## How answers are scored

Every answer maps to a risk value between 0.0 (no added risk) and 1.0 (maximum added risk).

| Scale | Used for | Answer -> risk value |
|---|---|---|
| `EXPOSURE` | Is X visible / do you do X? (with Sometimes) | Yes = 1.0, Sometimes = 0.5, No = 0.0, Not sure = 0.6 |
| `EXPOSURE_YN` | Is X visible? (yes/no) | Yes = 1.0, No = 0.0, Not sure = 0.6 |
| `PROTECTIVE` | Do you use control X? (with Sometimes; NO is risky) | Yes = 0.0, Sometimes = 0.5, No = 1.0, Not sure = 0.7 |
| `PROTECTIVE_YN` | Is control X enabled? (NO is risky) | Yes = 0.0, No = 1.0, Not sure = 0.7 |
| `VISIBILITY` | Audience settings | Public = 1.0, Friends / followers only = 0.4, Private / only me = 0.0, Not sure = 0.6 |
| `FREQUENCY` | How often do you do X? | Always = 1.0, Often = 0.75, Sometimes = 0.4, Never = 0.0 |
| `RECENCY` | When did you last review X? | Within the last 3 months = 0.0, Within the last year = 0.3, More than a year ago = 0.7, Never = 1.0 |

`Not sure` is scored as moderate risk on purpose: you cannot rely on a setting you cannot confirm.

**Weight** is the question's importance inside its category (1.0-3.0). **Impact** is the potential harm if the weakness is abused and drives finding severity.

## Category A: Profile Visibility

Who can see and discover your profile.

| # | Question | Answers | Weight | Impact | Feature id |
|---|---|---|---|---|---|
| A1 | Who can see your main profile (bio, photos, details)? | PUBLIC / FRIENDS / FOLLOWERS ONLY / PRIVATE / ONLY ME / NOT SURE | 3.0 | MEDIUM | `profile_visibility` |
| A2 | Can search engines (e.g. Google) link directly to your profile? | YES / NO / NOT SURE | 2.0 | MEDIUM | `search_engine_indexing` |
| A3 | Who can see your friends / followers list? | PUBLIC / FRIENDS / FOLLOWERS ONLY / PRIVATE / ONLY ME / NOT SURE | 1.5 | LOW | `friends_list_visibility` |
| A4 | Can people find your profile by searching your phone number or email? | YES / NO / NOT SURE | 1.5 | MEDIUM | `discoverable_by_contact` |
| A5 | Does your public profile picture clearly show your face or identifiable surroundings (home, school, workplace)? | YES / NO / NOT SURE | 1.0 | LOW | `identifiable_profile_photo` |

## Category B: Personal Information

Contact details, birthday, home, work, education and family information.

| # | Question | Answers | Weight | Impact | Feature id |
|---|---|---|---|---|---|
| B6 | Is your phone number publicly visible on your profile? | YES / NO / NOT SURE | 3.0 | HIGH | `phone_public` |
| B7 | Is your personal email address publicly visible? | YES / NO / NOT SURE | 2.0 | MEDIUM | `email_public` |
| B8 | Is your FULL birth date (day, month AND year) publicly visible? | YES / NO / NOT SURE | 2.5 | MEDIUM | `birthday_public` |
| B9 | Is your home address, street or neighbourhood publicly visible or easy to work out from your profile? | YES / NO / NOT SURE | 3.0 | HIGH | `home_info_public` |
| B10 | Is your current workplace publicly visible? | YES / NO / NOT SURE | 1.5 | MEDIUM | `workplace_public` |
| B11 | Is your school / college publicly visible? | YES / NO / NOT SURE | 1.0 | LOW | `education_public` |
| B12 | Are your relationship status or family members' details publicly visible? | YES / NO / NOT SURE | 1.5 | MEDIUM | `relationship_public` |

## Category C: Location Privacy

Real-time location, geotags, check-ins, travel and routine patterns.

| # | Question | Answers | Weight | Impact | Feature id |
|---|---|---|---|---|---|
| C13 | Is your current city or home location shown publicly on your profile? | YES / NO / NOT SURE | 2.0 | MEDIUM | `location_public` |
| C14 | Do you share your real-time / live location publicly or with a large audience? | YES / SOMETIMES / NO / NOT SURE | 3.0 | HIGH | `realtime_location_sharing` |
| C15 | How often do your posts include a location tag / geotag? | ALWAYS / OFTEN / SOMETIMES / NEVER | 2.0 | MEDIUM | `geotagging` |
| C16 | How often do you post check-ins while you are still at the location? | ALWAYS / OFTEN / SOMETIMES / NEVER | 2.0 | HIGH | `realtime_checkins` |
| C17 | Do you publicly post travel plans before or during a trip? | YES / SOMETIMES / NO / NOT SURE | 2.5 | HIGH | `travel_posts` |
| C18 | Do your posts reveal routine locations (gym, school, commute) on a regular pattern? | YES / SOMETIMES / NO / NOT SURE | 2.0 | MEDIUM | `routine_locations` |

## Category D: Posts & Content

Who sees your posts and what your photos reveal.

| # | Question | Answers | Weight | Impact | Feature id |
|---|---|---|---|---|---|
| D19 | What is the default audience for your new posts? | PUBLIC / FRIENDS / FOLLOWERS ONLY / PRIVATE / ONLY ME / NOT SURE | 3.0 | MEDIUM | `posts_visibility` |
| D20 | Do your photos sometimes show ID badges, documents, computer screens, vehicle plates or school uniforms? | YES / SOMETIMES / NO / NOT SURE | 2.0 | HIGH | `photo_sensitive_details` |
| D21 | Do you check or remove photo metadata (EXIF, e.g. GPS) before sharing original image files? | YES / SOMETIMES / NO / NOT SURE | 1.5 | MEDIUM | `photo_metadata_checked` |
| D22 | Are your stories / status updates visible to everyone? | YES / SOMETIMES / NO / NOT SURE | 1.5 | MEDIUM | `stories_public` |
| D23 | Do you publicly post photos that identify family members or children? | YES / SOMETIMES / NO / NOT SURE | 1.5 | MEDIUM | `family_photos_public` |

## Category E: Friends / Followers

How you accept and manage connections.

| # | Question | Answers | Weight | Impact | Feature id |
|---|---|---|---|---|---|
| E24 | How often do you accept connection / friend requests from people you do not know? | ALWAYS / OFTEN / SOMETIMES / NEVER | 3.0 | HIGH | `unknown_connections` |
| E25 | Do you verify unfamiliar profiles (mutual contacts, account age, activity) before accepting? | YES / SOMETIMES / NO / NOT SURE | 2.0 | MEDIUM | `verify_unknown_profiles` |
| E26 | Do you periodically review and remove connections you no longer know or trust? | YES / SOMETIMES / NO / NOT SURE | 1.5 | LOW | `connections_reviewed` |
| E27 | Do new followers need your approval before they can see your content? | YES / NO / NOT SURE | 1.5 | LOW | `follower_approval` |

## Category F: Tagging & Mentions

How other people can attach you to their content.

| # | Question | Answers | Weight | Impact | Feature id |
|---|---|---|---|---|---|
| F28 | Can anyone tag you in posts or photos? | YES / NO / NOT SURE | 2.0 | MEDIUM | `anyone_can_tag` |
| F29 | Is tag review / approval enabled before tags appear on your profile? | YES / NO / NOT SURE | 3.0 | MEDIUM | `tag_review_enabled` |
| F30 | Do posts you are tagged in appear on your profile automatically? | YES / NO / NOT SURE | 1.5 | LOW | `tagged_posts_auto_visible` |
| F31 | Can accounts you do not know @mention you? | YES / NO / NOT SURE | 1.0 | LOW | `unknown_mentions` |

## Category G: Authentication & Account Security

MFA, passwords, login alerts, recovery and sessions.

| # | Question | Answers | Weight | Impact | Feature id |
|---|---|---|---|---|---|
| G32 | Is multi-factor authentication (MFA / 2-step verification) enabled on your account? | YES / NO / NOT SURE | 3.0 | HIGH | `mfa_enabled` |
| G33 | Do you use the same password for this account and any other website or app? | YES / NO / NOT SURE | 3.0 | HIGH | `password_reuse` |
| G34 | Do you use a password manager to create and store unique passwords? | YES / NO / NOT SURE | 1.5 | MEDIUM | `password_manager_used` |
| G35 | Are login alerts (notifications of new sign-ins) enabled? | YES / NO / NOT SURE | 2.0 | MEDIUM | `login_alerts_enabled` |
| G36 | Have you checked your account recovery email / phone in the last 12 months? | YES / NO / NOT SURE | 1.5 | MEDIUM | `recovery_info_reviewed` |
| G37 | Do you review active sessions / logged-in devices and sign out of unknown ones? | YES / SOMETIMES / NO / NOT SURE | 1.5 | MEDIUM | `active_sessions_reviewed` |

## Category H: Third-Party Apps

Apps and websites connected to your account.

| # | Question | Answers | Weight | Impact | Feature id |
|---|---|---|---|---|---|
| H38 | Do you review the third-party apps and websites connected to your account? | YES / SOMETIMES / NO / NOT SURE | 3.0 | MEDIUM | `third_party_apps_reviewed` |
| H39 | Are there apps connected to your account that you no longer use? | YES / NO / NOT SURE | 2.0 | MEDIUM | `unused_apps_connected` |
| H40 | How often do you use 'Sign in with <social account>' on other websites? | ALWAYS / OFTEN / SOMETIMES / NEVER | 1.5 | LOW | `social_login_usage` |
| H41 | Do you grant permissions to quizzes, games or personality-test apps? | YES / SOMETIMES / NO / NOT SURE | 1.5 | MEDIUM | `quiz_app_permissions` |

## Category I: Messaging & Social Engineering

How you handle unexpected messages, links and requests.

| # | Question | Answers | Weight | Impact | Feature id |
|---|---|---|---|---|---|
| I42 | Before clicking a link in a message, do you check where it really leads? | YES / SOMETIMES / NO / NOT SURE | 2.0 | HIGH | `suspicious_link_awareness` |
| I43 | How often do you respond to unexpected messages from unknown accounts asking for information? | ALWAYS / OFTEN / SOMETIMES / NEVER | 2.0 | MEDIUM | `respond_unknown_dms` |
| I44 | Have you ever shared a verification / OTP code with someone who asked for it? | YES / NO / NOT SURE | 3.0 | HIGH | `verification_code_shared` |
| I45 | When a 'friend' urgently asks for money or help by message, do you confirm through another channel (e.g. a call)? | YES / SOMETIMES / NO / NOT SURE | 2.0 | HIGH | `impersonation_verified` |
| I46 | How often do you join giveaways that ask for personal details or external links? | ALWAYS / OFTEN / SOMETIMES / NEVER | 1.5 | MEDIUM | `giveaway_participation` |
| I47 | How often do you share personal details (address, ID numbers, account details) in direct messages? | ALWAYS / OFTEN / SOMETIMES / NEVER | 2.0 | HIGH | `personal_info_in_dms` |

## Category J: Digital Footprint

Old posts, old accounts, public comments and review habits.

| # | Question | Answers | Weight | Impact | Feature id |
|---|---|---|---|---|---|
| J48 | Do you regularly review and clean up your old public posts? | YES / SOMETIMES / NO / NOT SURE | 2.5 | MEDIUM | `old_posts_reviewed` |
| J49 | Do you have old or unused social-media accounts that are still active? | YES / NO / NOT SURE | 2.0 | MEDIUM | `old_accounts_active` |
| J50 | How often do you comment publicly using an identifiable name? | ALWAYS / OFTEN / SOMETIMES / NEVER | 1.5 | LOW | `public_comments` |
| J51 | When did you last review your privacy settings? | WITHIN THE LAST 3 MONTHS / WITHIN THE LAST YEAR / MORE THAN A YEAR AGO / NEVER | 2.5 | MEDIUM | `privacy_settings_reviewed` |
| J52 | Do you use the same username on many platforms? | YES / SOMETIMES / NO / NOT SURE | 1.0 | LOW | `same_username_everywhere` |
| J53 | Have you ever searched your own name to see what is publicly visible about you? | YES / NO / NOT SURE | 1.0 | LOW | `self_search_done` |
