"""
Social Media Privacy Checklist.

A static, printable checklist served by GET /api/privacy-checklist and shown
on frontend/checklist.html. `related_findings` links each item to the
questionnaire so the UI can highlight items relevant to the user's findings.
"""

PRIVACY_CHECKLIST = [
    {"id": 1, "item": "Review profile visibility", "area": "Profile",
     "tip": "Decide which profile sections truly need to be public.",
     "related_findings": ["profile_visibility", "search_engine_indexing"]},
    {"id": 2, "item": "Hide unnecessary contact information", "area": "Personal Info",
     "tip": "Phone numbers and personal email rarely need to be public.",
     "related_findings": ["phone_public", "email_public", "discoverable_by_contact"]},
    {"id": 3, "item": "Review birth-date visibility", "area": "Personal Info",
     "tip": "Hide the birth year or the full date.",
     "related_findings": ["birthday_public"]},
    {"id": 4, "item": "Review location sharing", "area": "Location",
     "tip": "Check live-location, geotag and hometown settings.",
     "related_findings": ["location_public", "realtime_location_sharing", "geotagging"]},
    {"id": 5, "item": "Avoid unnecessary real-time location posts", "area": "Location",
     "tip": "Post after you leave; share travel after you return.",
     "related_findings": ["realtime_checkins", "travel_posts", "routine_locations"]},
    {"id": 6, "item": "Review tagging permissions", "area": "Tagging",
     "tip": "Enable tag review and limit who can tag or mention you.",
     "related_findings": ["tag_review_enabled", "anyone_can_tag", "tagged_posts_auto_visible"]},
    {"id": 7, "item": "Review followers / friends", "area": "Connections",
     "tip": "Remove connections you no longer know or trust.",
     "related_findings": ["connections_reviewed", "follower_approval"]},
    {"id": 8, "item": "Verify unfamiliar requests", "area": "Connections",
     "tip": "Check mutual contacts, account age and activity first.",
     "related_findings": ["unknown_connections", "verify_unknown_profiles"]},
    {"id": 9, "item": "Enable MFA", "area": "Account Security",
     "tip": "Prefer an authenticator app or security key over SMS where supported.",
     "related_findings": ["mfa_enabled"]},
    {"id": 10, "item": "Enable login alerts where available", "area": "Account Security",
     "tip": "Get notified about new sign-ins.",
     "related_findings": ["login_alerts_enabled"]},
    {"id": 11, "item": "Review active sessions", "area": "Account Security",
     "tip": "Sign out of devices you do not recognise.",
     "related_findings": ["active_sessions_reviewed", "recovery_info_reviewed"]},
    {"id": 12, "item": "Review connected apps", "area": "Third-Party Apps",
     "tip": "Apply least privilege - keep only what you need.",
     "related_findings": ["third_party_apps_reviewed", "quiz_app_permissions"]},
    {"id": 13, "item": "Remove unused integrations", "area": "Third-Party Apps",
     "tip": "Revoke apps you no longer use.",
     "related_findings": ["unused_apps_connected", "social_login_usage"]},
    {"id": 14, "item": "Review old public posts", "area": "Digital Footprint",
     "tip": "Archive, restrict or delete old content you no longer want public.",
     "related_findings": ["old_posts_reviewed", "old_accounts_active"]},
    {"id": 15, "item": "Review photo privacy", "area": "Content",
     "tip": "Check backgrounds and remove metadata from original files.",
     "related_findings": ["photo_sensitive_details", "photo_metadata_checked", "family_photos_public"]},
    {"id": 16, "item": "Be cautious with unexpected links", "area": "Social Engineering",
     "tip": "Open the official app or type the address yourself.",
     "related_findings": ["suspicious_link_awareness", "giveaway_participation"]},
    {"id": 17, "item": "Never share verification codes", "area": "Social Engineering",
     "tip": "No legitimate service or friend needs your OTP.",
     "related_findings": ["verification_code_shared", "impersonation_verified"]},
    {"id": 18, "item": "Review privacy settings periodically", "area": "Digital Footprint",
     "tip": "Set a reminder every 3-6 months.",
     "related_findings": ["privacy_settings_reviewed", "self_search_done"]},
]


def get_checklist(finding_types=None):
    """Return the checklist; items linked to the given finding types are flagged."""
    finding_set = set(finding_types or [])
    return [
        {**item, "relevant": bool(finding_set.intersection(item["related_findings"]))}
        for item in PRIVACY_CHECKLIST
    ]
