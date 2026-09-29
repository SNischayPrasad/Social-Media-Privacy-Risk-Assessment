"""
Fictional demonstration profiles.

These are NOT real people. They are hand-written answer sets used for the
safe demonstration (README section "Safe Demonstration Profile"), for tests,
and as anchors for the synthetic dataset generator.
"""

from backend.services.questionnaire import QUESTIONS, SCALES, safest_answer


def fully_private_profile():
    """Every question answered with its lowest-risk option."""
    return {q["id"]: safest_answer(q["id"]) for q in QUESTIONS}


def fully_public_profile():
    """Every question answered with its highest-risk option."""
    return {
        q["id"]: max(q["options"], key=lambda option: SCALES[q["scale"]][option])
        for q in QUESTIONS
    }


# "Demo Riya" - a fictional, over-sharing student profile (section 32 of the brief).
# Answers explicitly listed in the brief are marked with  # brief
DEMO_PROFILE = {
    # A. Profile
    "profile_visibility": "PUBLIC",            # brief: Profile public
    "search_engine_indexing": "YES",
    "friends_list_visibility": "PUBLIC",
    "discoverable_by_contact": "YES",
    "identifiable_profile_photo": "YES",
    # B. Personal information
    "phone_public": "YES",                     # brief: Phone public
    "email_public": "NO",                      # brief: Email private
    "birthday_public": "YES",                  # brief: Full birthday public
    "home_info_public": "NOT_SURE",
    "workplace_public": "YES",
    "education_public": "YES",
    "relationship_public": "YES",
    # C. Location
    "location_public": "YES",                  # brief: Location public
    "realtime_location_sharing": "YES",        # brief: Real-time check-ins yes
    "geotagging": "OFTEN",
    "realtime_checkins": "OFTEN",
    "travel_posts": "YES",                     # brief: Travel plans public
    "routine_locations": "SOMETIMES",
    # D. Content
    "posts_visibility": "PUBLIC",
    "photo_sensitive_details": "SOMETIMES",
    "photo_metadata_checked": "NO",
    "stories_public": "YES",
    "family_photos_public": "SOMETIMES",
    # E. Connections
    "unknown_connections": "OFTEN",            # brief: Unknown requests often accepted
    "verify_unknown_profiles": "NO",
    "connections_reviewed": "NO",
    "follower_approval": "NO",
    # F. Tagging
    "anyone_can_tag": "YES",
    "tag_review_enabled": "NO",                # brief: Tag review disabled
    "tagged_posts_auto_visible": "YES",
    "unknown_mentions": "YES",
    # G. Account security
    "mfa_enabled": "NO",                       # brief: MFA disabled
    "password_reuse": "NOT_SURE",
    "password_manager_used": "NO",
    "login_alerts_enabled": "NO",              # brief: Login alerts disabled
    "recovery_info_reviewed": "NO",
    "active_sessions_reviewed": "NO",
    # H. Third-party apps
    "third_party_apps_reviewed": "NO",         # brief: Third-party apps not reviewed
    "unused_apps_connected": "NOT_SURE",
    "social_login_usage": "OFTEN",
    "quiz_app_permissions": "SOMETIMES",
    # I. Social engineering
    "suspicious_link_awareness": "SOMETIMES",
    "respond_unknown_dms": "SOMETIMES",
    "verification_code_shared": "NO",
    "impersonation_verified": "SOMETIMES",
    "giveaway_participation": "SOMETIMES",
    "personal_info_in_dms": "SOMETIMES",
    # J. Digital footprint
    "old_posts_reviewed": "NO",                # brief: Old posts not reviewed
    "old_accounts_active": "YES",
    "public_comments": "OFTEN",
    "privacy_settings_reviewed": "NEVER",
    "same_username_everywhere": "YES",
    "self_search_done": "NO",
}

# The improvements listed in section 32 of the brief.
DEMO_IMPROVEMENTS = {
    "phone_public": "NO",                  # Phone -> Private
    "birthday_public": "NO",               # Birthday -> Private
    "location_public": "NO",               # Location -> Private
    "realtime_location_sharing": "NO",     # (Location -> Private includes live location)
    "travel_posts": "NO",                  # Travel plans -> Private
    "unknown_connections": "NEVER",        # Unknown requests -> Reject / verify
    "verify_unknown_profiles": "YES",
    "tag_review_enabled": "YES",           # Tag review -> Enabled
    "mfa_enabled": "YES",                  # MFA -> Enabled
    "login_alerts_enabled": "YES",         # Login alerts -> Enabled
    "third_party_apps_reviewed": "YES",    # Third-party apps -> Reviewed
}
