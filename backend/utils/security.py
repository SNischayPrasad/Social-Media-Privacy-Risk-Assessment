"""
Security helpers: HTTP security headers and a simple in-memory rate limiter.

SECURITY HEADERS
    Content-Security-Policy  - only allow scripts from this site and the Chart.js CDN;
                               blocks inline scripts, which stops most XSS payloads.
    X-Content-Type-Options   - stops browsers guessing (sniffing) content types.
    X-Frame-Options / frame-ancestors - prevents click-jacking via iframes.
    Referrer-Policy          - does not leak page URLs (which contain assessment IDs).
    Permissions-Policy       - the app never needs camera, microphone or geolocation.
    Cache-Control: no-store  - API responses are not cached by browsers/proxies.

RATE LIMITING
    A sliding-window limiter keyed by client IP. It is intentionally simple
    (in-memory, single process) for a student project. Production systems would
    use a shared store such as Redis or a gateway/WAF. The IP is held in memory
    only for the window duration and is never written to disk or logs.
"""

import threading
import time
from collections import defaultdict, deque
from functools import wraps

from flask import current_app, jsonify, request

CDN = "https://cdn.jsdelivr.net"

APP_CSP = (
    "default-src 'self'; "
    f"script-src 'self' {CDN}; "
    "style-src 'self' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)

# Reports contain inline CSS but NO scripts at all.
REPORT_CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src data:; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


def apply_security_headers(response):
    """Attach security headers to every response (registered as an after_request hook)."""
    if not response.headers.get("Content-Security-Policy"):
        response.headers["Content-Security-Policy"] = APP_CSP
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


class RateLimiter:
    """Sliding-window rate limiter: at most `limit` requests per `window` seconds per key."""

    def __init__(self):
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key, limit, window=60):
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > window:
                hits.popleft()
            if len(hits) >= limit:
                return False, int(window - (now - hits[0])) + 1
            hits.append(now)
            return True, 0

    def reset(self):
        with self._lock:
            self._hits.clear()


rate_limiter = RateLimiter()


def rate_limited(func):
    """Decorator: apply the configured per-minute limit to an endpoint."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        limit = current_app.config["RATE_LIMIT_PER_MINUTE"]
        if limit > 0:
            key = f"{request.remote_addr}:{request.endpoint}"
            allowed, retry_after = rate_limiter.allow(key, limit)
            if not allowed:
                response = jsonify(error="Too many requests. Please slow down and try again shortly.")
                response.status_code = 429
                response.headers["Retry-After"] = str(retry_after)
                return response
        return func(*args, **kwargs)

    return wrapper
