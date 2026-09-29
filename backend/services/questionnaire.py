"""
Privacy Assessment Questionnaire (single source of truth).

Every question the user sees, every answer they may choose, and the risk value
each answer contributes are defined HERE. The frontend downloads this list
through GET /api/questionnaire, so the UI and the scoring engine can never
drift apart.

PRIVACY NOTE
------------
No question ever asks for the sensitive value itself. We ask "Is your phone
number publicly visible?" - never "What is your phone number?". This lets us
assess exposure without collecting personal data (data minimisation).

HOW ANSWERS BECOME RISK
-----------------------
Each question uses an answer *scale*. A scale maps every allowed answer to a
risk value between 0.0 (no added risk) and 1.0 (maximum added risk):

    EXPOSURE    - "Is X publicly visible?"  YES is risky.
    PROTECTIVE  - "Is control X enabled?"   NO is risky (inverse question).
    VISIBILITY  - PUBLIC / FRIENDS / PRIVATE.
    FREQUENCY   - ALWAYS / OFTEN / SOMETIMES / NEVER.
    RECENCY     - how long ago something was reviewed.

"NOT_SURE" is deliberately scored as moderate risk: if you do not know whether
a setting is on, you cannot rely on it.

Each question also has:
    weight  - importance of the question *inside its category* (1.0 - 3.0)
    impact  - HIGH / MEDIUM / LOW potential impact if the weakness is abused
    finding - short, non-sensitive text used when the answer is risky
"""

# --------------------------------------------------------------------------
# Answer scales: answer -> risk value (0.0 = safest, 1.0 = riskiest)
# --------------------------------------------------------------------------
SCALES = {
    "EXPOSURE": {"YES": 1.0, "SOMETIMES": 0.5, "NO": 0.0, "NOT_SURE": 0.6},
    "EXPOSURE_YN": {"YES": 1.0, "NO": 0.0, "NOT_SURE": 0.6},
    "PROTECTIVE": {"YES": 0.0, "SOMETIMES": 0.5, "NO": 1.0, "NOT_SURE": 0.7},
    "PROTECTIVE_YN": {"YES": 0.0, "NO": 1.0, "NOT_SURE": 0.7},
    "VISIBILITY": {"PUBLIC": 1.0, "FRIENDS": 0.4, "PRIVATE": 0.0, "NOT_SURE": 0.6},
    "FREQUENCY": {"ALWAYS": 1.0, "OFTEN": 0.75, "SOMETIMES": 0.4, "NEVER": 0.0},
    "RECENCY": {"WITHIN_3_MONTHS": 0.0, "WITHIN_YEAR": 0.3, "OVER_A_YEAR": 0.7, "NEVER": 1.0},
}

# Human-friendly labels for answer codes (used by the frontend and report).
ANSWER_LABELS = {
    "YES": "Yes",
    "NO": "No",
    "SOMETIMES": "Sometimes",
    "NOT_SURE": "Not sure",
    "PUBLIC": "Public",
    "FRIENDS": "Friends / followers only",
    "PRIVATE": "Private / only me",
    "ALWAYS": "Always",
    "OFTEN": "Often",
    "NEVER": "Never",
    "WITHIN_3_MONTHS": "Within the last 3 months",
    "WITHIN_YEAR": "Within the last year",
    "OVER_A_YEAR": "More than a year ago",
}

# --------------------------------------------------------------------------
# The ten risk categories (A - J)
# --------------------------------------------------------------------------
CATEGORIES = {
    "profile_exposure": {
        "code": "A",
        "name": "Profile Visibility",
        "short": "Profile",
        "description": "Who can see and discover your profile.",
    },
    "personal_information": {
        "code": "B",
        "name": "Personal Information",
        "short": "Personal Info",
        "description": "Contact details, birthday, home, work, education and family information.",
    },
    "location_exposure": {
        "code": "C",
        "name": "Location Privacy",
        "short": "Location",
        "description": "Real-time location, geotags, check-ins, travel and routine patterns.",
    },
    "content_exposure": {
        "code": "D",
        "name": "Posts & Content",
        "short": "Content",
        "description": "Who sees your posts and what your photos reveal.",
    },
    "connection_risk": {
        "code": "E",
        "name": "Friends / Followers",
        "short": "Connections",
        "description": "How you accept and manage connections.",
    },
    "tagging_risk": {
        "code": "F",
        "name": "Tagging & Mentions",
        "short": "Tagging",
        "description": "How other people can attach you to their content.",
    },
    "account_security": {
        "code": "G",
        "name": "Authentication & Account Security",
        "short": "Account Security",
        "description": "MFA, passwords, login alerts, recovery and sessions.",
    },
    "third_party_apps": {
        "code": "H",
        "name": "Third-Party Apps",
        "short": "Third-Party Apps",
        "description": "Apps and websites connected to your account.",
    },
    "social_engineering": {
        "code": "I",
        "name": "Messaging & Social Engineering",
        "short": "Social Engineering",
        "description": "How you handle unexpected messages, links and requests.",
    },
    "digital_footprint": {
        "code": "J",
        "name": "Digital Footprint",
        "short": "Digital Footprint",
        "description": "Old posts, old accounts, public comments and review habits.",
    },
}


def _q(qid, category, text, scale, weight, impact, finding, help_text, options=None):
    """Small helper that builds one question dictionary.

    `options` lets a question use only a subset of its scale's answers
    (for example YES / NO / NOT_SURE without SOMETIMES).
    """
    allowed = options or list(SCALES[scale].keys())
    return {
        "id": qid,
        "category": category,
        "text": text,
        "scale": scale,
        "options": allowed,
        "weight": weight,
        "impact": impact,
        "finding": finding,
        "help": help_text,
    }


# --------------------------------------------------------------------------
# QUESTIONS (53 total)
# The `id` is also the feature name used by the engines and the dataset.
# --------------------------------------------------------------------------
QUESTIONS = [
    # ---------------- A. PROFILE VISIBILITY ----------------
    _q("profile_visibility", "profile_exposure",
       "Who can see your main profile (bio, photos, details)?",
       "VISIBILITY", 3.0, "MEDIUM",
       "Profile is publicly visible",
       "A public profile is not automatically unsafe, but everything on it can be seen by anyone."),
    _q("search_engine_indexing", "profile_exposure",
       "Can search engines (e.g. Google) link directly to your profile?",
       "EXPOSURE_YN", 2.0, "MEDIUM",
       "Profile can be indexed by search engines",
       "Search-engine indexing makes your profile discoverable by people who never used the platform."),
    _q("friends_list_visibility", "profile_exposure",
       "Who can see your friends / followers list?",
       "VISIBILITY", 1.5, "LOW",
       "Friends / followers list is visible to everyone",
       "A visible friends list reveals your social circle, family and colleagues."),
    _q("discoverable_by_contact", "profile_exposure",
       "Can people find your profile by searching your phone number or email?",
       "EXPOSURE_YN", 1.5, "MEDIUM",
       "Profile is discoverable by phone number or email",
       "Contact-based discovery links your phone/email to your profile identity."),
    _q("identifiable_profile_photo", "profile_exposure",
       "Does your public profile picture clearly show your face or identifiable surroundings (home, school, workplace)?",
       "EXPOSURE_YN", 1.0, "LOW",
       "Profile photo is clearly identifiable",
       "Identifiable photos make it easier for someone to recognise you or create an impersonation account."),

    # ---------------- B. PERSONAL INFORMATION ----------------
    _q("phone_public", "personal_information",
       "Is your phone number publicly visible on your profile?",
       "EXPOSURE_YN", 3.0, "HIGH",
       "Phone number reported as publicly visible",
       "Do NOT type your number. Only tell us whether it is visible."),
    _q("email_public", "personal_information",
       "Is your personal email address publicly visible?",
       "EXPOSURE_YN", 2.0, "MEDIUM",
       "Personal email reported as publicly visible",
       "Public email addresses attract spam and targeted phishing."),
    _q("birthday_public", "personal_information",
       "Is your FULL birth date (day, month AND year) publicly visible?",
       "EXPOSURE_YN", 2.5, "MEDIUM",
       "Full birth date reported as publicly visible",
       "Full birth dates are often used in identity verification and security questions."),
    _q("home_info_public", "personal_information",
       "Is your home address, street or neighbourhood publicly visible or easy to work out from your profile?",
       "EXPOSURE_YN", 3.0, "HIGH",
       "Home-related information reported as publicly visible",
       "Home-related details can affect physical safety as well as privacy."),
    _q("workplace_public", "personal_information",
       "Is your current workplace publicly visible?",
       "EXPOSURE_YN", 1.5, "MEDIUM",
       "Workplace reported as publicly visible",
       "Workplace details are commonly used to make business-related scams more convincing."),
    _q("education_public", "personal_information",
       "Is your school / college publicly visible?",
       "EXPOSURE_YN", 1.0, "LOW",
       "School / college reported as publicly visible",
       "Education details can be combined with other information to build a profile of you."),
    _q("relationship_public", "personal_information",
       "Are your relationship status or family members' details publicly visible?",
       "EXPOSURE_YN", 1.5, "MEDIUM",
       "Relationship / family details reported as publicly visible",
       "Family names are frequently used as security-question answers and in impersonation scams."),

    # ---------------- C. LOCATION PRIVACY ----------------
    _q("location_public", "location_exposure",
       "Is your current city or home location shown publicly on your profile?",
       "EXPOSURE_YN", 2.0, "MEDIUM",
       "Current city / home location shown publicly",
       "A city alone is low detail, but combined with other posts it narrows down where you live."),
    _q("realtime_location_sharing", "location_exposure",
       "Do you share your real-time / live location publicly or with a large audience?",
       "EXPOSURE", 3.0, "HIGH",
       "Real-time location sharing enabled for a broad audience",
       "Real-time location tells people where you are right now."),
    _q("geotagging", "location_exposure",
       "How often do your posts include a location tag / geotag?",
       "FREQUENCY", 2.0, "MEDIUM",
       "Posts frequently include location tags",
       "Frequent geotags build a map of the places you visit."),
    _q("realtime_checkins", "location_exposure",
       "How often do you post check-ins while you are still at the location?",
       "FREQUENCY", 2.0, "HIGH",
       "Real-time check-ins posted while still at the location",
       "Posting after you leave ('late posting') reduces immediate exposure."),
    _q("travel_posts", "location_exposure",
       "Do you publicly post travel plans before or during a trip?",
       "EXPOSURE", 2.5, "HIGH",
       "Travel plans shared publicly before or during trips",
       "Announcing a trip in advance can reveal when your home is empty."),
    _q("routine_locations", "location_exposure",
       "Do your posts reveal routine locations (gym, school, commute) on a regular pattern?",
       "EXPOSURE", 2.0, "MEDIUM",
       "Routine locations / patterns visible in posts",
       "Routines let someone predict where you will be and when."),

    # ---------------- D. POSTS & CONTENT ----------------
    _q("posts_visibility", "content_exposure",
       "What is the default audience for your new posts?",
       "VISIBILITY", 3.0, "MEDIUM",
       "Posts are public by default",
       "Default audience matters because most people never change it per post."),
    _q("photo_sensitive_details", "content_exposure",
       "Do your photos sometimes show ID badges, documents, computer screens, vehicle plates or school uniforms?",
       "EXPOSURE", 2.0, "HIGH",
       "Photos may reveal badges, documents, screens or plates",
       "Background details in photos often leak more than the photo's main subject."),
    _q("photo_metadata_checked", "content_exposure",
       "Do you check or remove photo metadata (EXIF, e.g. GPS) before sharing original image files?",
       "PROTECTIVE", 1.5, "MEDIUM",
       "Photo metadata is not checked before sharing",
       "Many platforms strip metadata, but files shared by email, chat or cloud links may keep it."),
    _q("stories_public", "content_exposure",
       "Are your stories / status updates visible to everyone?",
       "EXPOSURE", 1.5, "MEDIUM",
       "Stories / status updates visible to everyone",
       "Stories are often more spontaneous and more revealing than regular posts."),
    _q("family_photos_public", "content_exposure",
       "Do you publicly post photos that identify family members or children?",
       "EXPOSURE", 1.5, "MEDIUM",
       "Identifiable family / children photos posted publicly",
       "Photos of others also affect their privacy; children cannot consent."),

    # ---------------- E. FRIENDS / FOLLOWERS ----------------
    _q("unknown_connections", "connection_risk",
       "How often do you accept connection / friend requests from people you do not know?",
       "FREQUENCY", 3.0, "HIGH",
       "Unknown connection requests frequently accepted",
       "Once accepted, a stranger may see everything shared with 'friends'."),
    _q("verify_unknown_profiles", "connection_risk",
       "Do you verify unfamiliar profiles (mutual contacts, account age, activity) before accepting?",
       "PROTECTIVE", 2.0, "MEDIUM",
       "Unfamiliar profiles not verified before accepting",
       "Fake profiles often have few posts, a new account and stolen photos."),
    _q("connections_reviewed", "connection_risk",
       "Do you periodically review and remove connections you no longer know or trust?",
       "PROTECTIVE", 1.5, "LOW",
       "Connections / followers are never reviewed",
       "Old connections keep access to content you share with 'friends'."),
    _q("follower_approval", "connection_risk",
       "Do new followers need your approval before they can see your content?",
       "PROTECTIVE_YN", 1.5, "LOW",
       "Follower approval is not required",
       "Approval gives you a chance to decide who sees your content."),

    # ---------------- F. TAGGING & MENTIONS ----------------
    _q("anyone_can_tag", "tagging_risk",
       "Can anyone tag you in posts or photos?",
       "EXPOSURE_YN", 2.0, "MEDIUM",
       "Anyone can tag you in posts or photos",
       "Tags from others can expose you even if you post very little yourself."),
    _q("tag_review_enabled", "tagging_risk",
       "Is tag review / approval enabled before tags appear on your profile?",
       "PROTECTIVE_YN", 3.0, "MEDIUM",
       "Tag review is disabled",
       "Tag review lets you approve or reject tags before they are linked to you."),
    _q("tagged_posts_auto_visible", "tagging_risk",
       "Do posts you are tagged in appear on your profile automatically?",
       "EXPOSURE_YN", 1.5, "LOW",
       "Tagged posts appear on your profile automatically",
       "Automatic display puts other people's content on your profile."),
    _q("unknown_mentions", "tagging_risk",
       "Can accounts you do not know @mention you?",
       "EXPOSURE_YN", 1.0, "LOW",
       "Unknown accounts can mention you",
       "Mentions from unknown accounts are a common spam and scam vector."),

    # ---------------- G. AUTHENTICATION & ACCOUNT SECURITY ----------------
    _q("mfa_enabled", "account_security",
       "Is multi-factor authentication (MFA / 2-step verification) enabled on your account?",
       "PROTECTIVE_YN", 3.0, "HIGH",
       "Multi-factor authentication (MFA) is disabled",
       "MFA means a stolen password alone is usually not enough to log in."),
    _q("password_reuse", "account_security",
       "Do you use the same password for this account and any other website or app?",
       "EXPOSURE_YN", 3.0, "HIGH",
       "Password reuse reported",
       "If any site that shares your password is breached, this account is at risk too. Never type your password here."),
    _q("password_manager_used", "account_security",
       "Do you use a password manager to create and store unique passwords?",
       "PROTECTIVE_YN", 1.5, "MEDIUM",
       "No password manager used",
       "Password managers make unique, strong passwords practical."),
    _q("login_alerts_enabled", "account_security",
       "Are login alerts (notifications of new sign-ins) enabled?",
       "PROTECTIVE_YN", 2.0, "MEDIUM",
       "Login alerts are disabled",
       "Login alerts help you notice an unauthorised sign-in quickly."),
    _q("recovery_info_reviewed", "account_security",
       "Have you checked your account recovery email / phone in the last 12 months?",
       "PROTECTIVE_YN", 1.5, "MEDIUM",
       "Account recovery information not reviewed recently",
       "Outdated recovery details can lock you out or let someone else recover your account."),
    _q("active_sessions_reviewed", "account_security",
       "Do you review active sessions / logged-in devices and sign out of unknown ones?",
       "PROTECTIVE", 1.5, "MEDIUM",
       "Active sessions / devices are not reviewed",
       "Old sessions on shared or lost devices can keep your account open."),

    # ---------------- H. THIRD-PARTY APPS ----------------
    _q("third_party_apps_reviewed", "third_party_apps",
       "Do you review the third-party apps and websites connected to your account?",
       "PROTECTIVE", 3.0, "MEDIUM",
       "Connected third-party apps are not reviewed",
       "Connected apps may keep access to your data long after you stop using them."),
    _q("unused_apps_connected", "third_party_apps",
       "Are there apps connected to your account that you no longer use?",
       "EXPOSURE_YN", 2.0, "MEDIUM",
       "Unused apps still connected to the account",
       "Unused integrations are unnecessary access (violates least privilege)."),
    _q("social_login_usage", "third_party_apps",
       "How often do you use 'Sign in with <social account>' on other websites?",
       "FREQUENCY", 1.5, "LOW",
       "Social-account sign-in used frequently",
       "Each social login creates a link between the site and your social account."),
    _q("quiz_app_permissions", "third_party_apps",
       "Do you grant permissions to quizzes, games or personality-test apps?",
       "EXPOSURE", 1.5, "MEDIUM",
       "Permissions granted to quiz / game apps",
       "Quiz apps often request more profile data than they need."),

    # ---------------- I. MESSAGING & SOCIAL ENGINEERING ----------------
    _q("suspicious_link_awareness", "social_engineering",
       "Before clicking a link in a message, do you check where it really leads?",
       "PROTECTIVE", 2.0, "HIGH",
       "Links in messages are clicked without checking",
       "Phishing links often imitate real login pages."),
    _q("respond_unknown_dms", "social_engineering",
       "How often do you respond to unexpected messages from unknown accounts asking for information?",
       "FREQUENCY", 2.0, "MEDIUM",
       "Responds to unexpected DMs from unknown accounts",
       "Unsolicited requests for information are a classic social-engineering pattern."),
    _q("verification_code_shared", "social_engineering",
       "Have you ever shared a verification / OTP code with someone who asked for it?",
       "EXPOSURE_YN", 3.0, "HIGH",
       "Verification codes have been shared with others",
       "No legitimate service or friend needs your verification code."),
    _q("impersonation_verified", "social_engineering",
       "When a 'friend' urgently asks for money or help by message, do you confirm through another channel (e.g. a call)?",
       "PROTECTIVE", 2.0, "HIGH",
       "Urgent requests are not verified through another channel",
       "Compromised or cloned accounts often send urgent requests to friends."),
    _q("giveaway_participation", "social_engineering",
       "How often do you join giveaways that ask for personal details or external links?",
       "FREQUENCY", 1.5, "MEDIUM",
       "Participates in giveaways requiring personal details",
       "Fake giveaways are used to collect personal data and spread links."),
    _q("personal_info_in_dms", "social_engineering",
       "How often do you share personal details (address, ID numbers, account details) in direct messages?",
       "FREQUENCY", 2.0, "HIGH",
       "Personal details shared over direct messages",
       "Messages can be forwarded, leaked or read by someone who took over the other account."),

    # ---------------- J. DIGITAL FOOTPRINT ----------------
    _q("old_posts_reviewed", "digital_footprint",
       "Do you regularly review and clean up your old public posts?",
       "PROTECTIVE", 2.5, "MEDIUM",
       "Old public posts are not reviewed",
       "Years of old posts can reveal far more than any single recent post."),
    _q("old_accounts_active", "digital_footprint",
       "Do you have old or unused social-media accounts that are still active?",
       "EXPOSURE_YN", 2.0, "MEDIUM",
       "Old / unused accounts are still active",
       "Forgotten accounts are rarely secured or monitored."),
    _q("public_comments", "digital_footprint",
       "How often do you comment publicly using an identifiable name?",
       "FREQUENCY", 1.5, "LOW",
       "Frequent public comments under an identifiable name",
       "Public comments are often indexed and remain searchable for years."),
    _q("privacy_settings_reviewed", "digital_footprint",
       "When did you last review your privacy settings?",
       "RECENCY", 2.5, "MEDIUM",
       "Privacy settings have not been reviewed recently",
       "Platforms change settings and defaults over time."),
    _q("same_username_everywhere", "digital_footprint",
       "Do you use the same username on many platforms?",
       "EXPOSURE", 1.0, "LOW",
       "Same username used across many platforms",
       "A shared username makes it easy to link your accounts together."),
    _q("self_search_done", "digital_footprint",
       "Have you ever searched your own name to see what is publicly visible about you?",
       "PROTECTIVE_YN", 1.0, "LOW",
       "Never checked what is publicly visible about you",
       "A self-search shows you what a stranger could find."),
]

# Fast lookup: question id -> question dictionary
QUESTION_INDEX = {q["id"]: q for q in QUESTIONS}


def get_questionnaire():
    """Return the questionnaire in a JSON-friendly structure for the frontend."""
    grouped = []
    for key, meta in CATEGORIES.items():
        grouped.append({
            "key": key,
            "code": meta["code"],
            "name": meta["name"],
            "description": meta["description"],
            "questions": [
                {
                    "id": q["id"],
                    "text": q["text"],
                    "help": q["help"],
                    "options": [{"value": o, "label": ANSWER_LABELS[o]} for o in q["options"]],
                }
                for q in QUESTIONS if q["category"] == key
            ],
        })
    return {"total_questions": len(QUESTIONS), "categories": grouped}


def answer_risk(question_id, answer):
    """Return the 0.0 - 1.0 risk value of one answer."""
    question = QUESTION_INDEX[question_id]
    return SCALES[question["scale"]][answer]


def safest_answer(question_id):
    """Return the lowest-risk allowed answer for a question (used by the simulator)."""
    question = QUESTION_INDEX[question_id]
    scale = SCALES[question["scale"]]
    return min(question["options"], key=lambda option: scale[option])
