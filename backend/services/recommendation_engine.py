"""
Recommendation Engine - personalised, prioritised privacy recommendations.

Each finding type has one defensive recommendation in RECOMMENDATION_CATALOG.
Recommendations are generated ONLY for the findings a user actually has,
so the list is personalised.

PRIORITY
    Derived from the finding's severity:
        HIGH   -> IMMEDIATE
        MEDIUM -> IMPORTANT
        LOW    -> GOOD_PRACTICE
    A few critical account-takeover controls have a minimum priority of
    IMMEDIATE regardless of severity (e.g. MFA disabled, password reuse,
    sharing verification codes).
"""

from backend.services.questionnaire import QUESTION_INDEX

PRIORITY_ORDER = ["IMMEDIATE", "IMPORTANT", "GOOD_PRACTICE"]
SEVERITY_TO_PRIORITY = {"HIGH": "IMMEDIATE", "MEDIUM": "IMPORTANT", "LOW": "GOOD_PRACTICE"}

# Findings that are always treated as IMMEDIATE.
ALWAYS_IMMEDIATE = {"mfa_enabled", "password_reuse", "verification_code_shared"}

# finding_type -> (recommendation, why it matters)
RECOMMENDATION_CATALOG = {
    # A. Profile visibility
    "profile_visibility": (
        "Review your profile audience and limit sections that do not need to be public.",
        "A public profile is visible to anyone, including people building a profile of you."),
    "search_engine_indexing": (
        "Turn off search-engine linking to your profile if the platform offers the option.",
        "Reduces discoverability by people outside the platform."),
    "friends_list_visibility": (
        "Restrict who can see your friends / followers list.",
        "Your connections reveal family, colleagues and schools."),
    "discoverable_by_contact": (
        "Disable 'find me by phone number / email' lookup settings.",
        "Prevents linking your contact details to your profile."),
    "identifiable_profile_photo": (
        "Consider a profile photo that does not reveal your home, school or workplace.",
        "Identifiable surroundings add location and affiliation context."),
    # B. Personal information
    "phone_public": (
        "Limit phone-number visibility to 'Only me' where possible.",
        "Public phone numbers enable spam calls, SMS phishing and account-recovery abuse."),
    "email_public": (
        "Hide your personal email, or use a separate contact address for public purposes.",
        "Public email addresses receive more targeted phishing."),
    "birthday_public": (
        "Hide your birth year or full birth date; show only day and month if you want greetings.",
        "Full birth dates are used in identity checks and security questions."),
    "home_info_public": (
        "Remove home address, street and neighbourhood details from your profile and posts.",
        "Home information affects physical safety as well as privacy."),
    "workplace_public": (
        "Limit workplace visibility to friends, or remove it if it is not needed.",
        "Workplace details make business-themed scams more convincing."),
    "education_public": (
        "Limit school / college visibility to friends.",
        "Education details help others piece together your identity."),
    "relationship_public": (
        "Limit relationship and family information to trusted audiences.",
        "Family names are common security-question answers and impersonation material."),
    # C. Location
    "location_public": (
        "Hide your current city / hometown or limit it to friends.",
        "Combined with other posts, a city narrows down where you live."),
    "realtime_location_sharing": (
        "Avoid publicly broadcasting real-time location unless intentionally needed; share live location only with specific trusted people.",
        "Real-time location reveals where you are right now."),
    "geotagging": (
        "Turn off automatic location tagging and add locations only when needed.",
        "Frequent geotags create a map of places you visit."),
    "realtime_checkins": (
        "Post check-ins and photos after you have left the location ('late posting').",
        "Delayed posting reduces immediate location exposure."),
    "travel_posts": (
        "Share travel photos after you return, or limit travel posts to close friends.",
        "Announcing trips can reveal when your home is empty."),
    "routine_locations": (
        "Avoid posting predictable routines (same gym, route or time every day).",
        "Routines let others predict where you will be."),
    # D. Content
    "posts_visibility": (
        "Change the default audience of new posts to Friends (or a custom list).",
        "Most posts inherit the default audience."),
    "photo_sensitive_details": (
        "Check photo backgrounds for badges, documents, screens, plates or uniforms before posting.",
        "Background details often leak more than the main subject."),
    "photo_metadata_checked": (
        "Remove metadata (EXIF / GPS) from original image files before sharing them outside the platform.",
        "Original files sent by email, chat or cloud links may keep location data."),
    "stories_public": (
        "Limit story / status audience to friends or a close-friends list.",
        "Stories are often more spontaneous and revealing."),
    "family_photos_public": (
        "Limit photos of family members and children to trusted audiences and ask for consent.",
        "Other people's privacy - especially children's - is affected by what you post."),
    # E. Connections
    "unknown_connections": (
        "Verify unfamiliar profiles before accepting connections; decline when unsure.",
        "Accepted strangers can see everything shared with friends."),
    "verify_unknown_profiles": (
        "Check mutual contacts, account age and activity before accepting a request.",
        "Fake profiles are commonly new, sparse and use stolen photos."),
    "connections_reviewed": (
        "Review your connections periodically and remove people you no longer know or trust.",
        "Old connections keep access to friends-only content."),
    "follower_approval": (
        "Enable follower approval / private account mode if available.",
        "Lets you decide who sees your content."),
    # F. Tagging
    "anyone_can_tag": (
        "Restrict who can tag you to friends (or nobody).",
        "Limits how others can attach you to their content."),
    "tag_review_enabled": (
        "Enable tag review so tags require your approval.",
        "You stay in control of what is linked to your profile."),
    "tagged_posts_auto_visible": (
        "Require review before tagged posts appear on your profile.",
        "Prevents other people's posts showing on your profile automatically."),
    "unknown_mentions": (
        "Limit mentions to people you follow or friends.",
        "Reduces spam and scam mentions."),
    # G. Account security
    "mfa_enabled": (
        "Enable multi-factor authentication using the strongest supported method (security key or authenticator app over SMS).",
        "MFA blocks most attacks that rely only on a stolen or guessed password."),
    "password_reuse": (
        "Use a unique password for this account; change it now if it is reused elsewhere.",
        "A breach on any other site could otherwise expose this account (credential stuffing)."),
    "password_manager_used": (
        "Use a reputable password manager to generate and store unique passwords.",
        "Makes unique, strong passwords practical for every account."),
    "login_alerts_enabled": (
        "Enable login alerts for new devices and locations where available.",
        "Helps you detect an unauthorised sign-in quickly."),
    "recovery_info_reviewed": (
        "Review your recovery email and phone number and remove old ones.",
        "Outdated recovery options can be abused or lock you out."),
    "active_sessions_reviewed": (
        "Review active sessions and sign out of devices you do not recognise.",
        "Old sessions on shared or lost devices keep your account open."),
    # H. Third-party apps
    "third_party_apps_reviewed": (
        "Review connected apps and revoke access you no longer need.",
        "Applies the Principle of Least Privilege to your account data."),
    "unused_apps_connected": (
        "Remove unused apps and old integrations from your account.",
        "Unused access is unnecessary risk."),
    "social_login_usage": (
        "Prefer separate accounts (with a password manager) over 'Sign in with social account' for non-essential sites.",
        "Reduces how many services depend on and link to your social account."),
    "quiz_app_permissions": (
        "Avoid granting profile permissions to quizzes and games.",
        "They often collect more data than they need."),
    # I. Social engineering
    "suspicious_link_awareness": (
        "Be cautious with unexpected links; open the official app or type the address yourself instead.",
        "Phishing links imitate real login pages."),
    "respond_unknown_dms": (
        "Do not share information with unknown accounts; verify identity first or ignore.",
        "Unsolicited requests for information are a common social-engineering pattern."),
    "verification_code_shared": (
        "Never share verification / OTP codes with anyone - legitimate services will not ask for them.",
        "Sharing a code can hand over your account even when MFA is enabled."),
    "impersonation_verified": (
        "Verify urgent requests from 'friends' through a separate channel such as a phone call.",
        "Cloned or compromised accounts are used to ask friends for money."),
    "giveaway_participation": (
        "Avoid giveaways that ask for personal details or external logins; check the account is official.",
        "Fake giveaways harvest personal data."),
    "personal_info_in_dms": (
        "Avoid sending ID numbers, addresses or account details over direct messages.",
        "Messages can be leaked, forwarded or read by an account takeover."),
    # J. Digital footprint
    "old_posts_reviewed": (
        "Review old public posts and archive, restrict or delete what you no longer want public.",
        "Historical posts add up to a detailed picture of you."),
    "old_accounts_active": (
        "Secure or delete old and unused accounts.",
        "Forgotten accounts are rarely monitored and may use old passwords."),
    "public_comments": (
        "Be mindful that public comments are searchable; limit personal details in them.",
        "Comments are often indexed and remain visible for years."),
    "privacy_settings_reviewed": (
        "Schedule a privacy-settings review every 3-6 months.",
        "Platforms change features and defaults over time."),
    "same_username_everywhere": (
        "Consider different usernames for personal and public accounts.",
        "Identical usernames make it easy to link your accounts."),
    "self_search_done": (
        "Search your own name and usernames to see what a stranger could find.",
        "You cannot reduce exposure you do not know about."),
}


def _priority_for(finding):
    priority = SEVERITY_TO_PRIORITY[finding["severity"]]
    if finding["finding_type"] in ALWAYS_IMMEDIATE:
        priority = "IMMEDIATE"
    return priority


def generate_recommendations(findings):
    """Build a prioritised recommendation list for the given findings.

    Returns:
        List of dicts: finding_type, category, risk, recommendation, why, priority.
        Sorted IMMEDIATE -> IMPORTANT -> GOOD_PRACTICE, keeping finding order inside a group.
    """
    recommendations = []
    for finding in findings:
        entry = RECOMMENDATION_CATALOG.get(finding["finding_type"])
        if not entry:
            continue
        text, why = entry
        recommendations.append({
            "finding_type": finding["finding_type"],
            "category": finding["category"],
            "risk": finding["title"],
            "recommendation": text,
            "why": why,
            "priority": _priority_for(finding),
        })

    recommendations.sort(key=lambda rec: PRIORITY_ORDER.index(rec["priority"]))
    return recommendations


def catalog_rows():
    """Rows used to seed the RECOMMENDATIONS table (finding_type, text, default priority)."""
    rows = []
    for finding_type, (text, _why) in RECOMMENDATION_CATALOG.items():
        default = SEVERITY_TO_PRIORITY[QUESTION_INDEX[finding_type]["impact"]]
        if finding_type in ALWAYS_IMMEDIATE:
            default = "IMMEDIATE"
        rows.append((finding_type, text, default))
    return rows
