"""
security.py
Security headers on every response, per-client rate limits on the scoring
endpoints, and a cap on how many LIME explanations run at once.
Author: Colile Sibanda

Limits are read from environment variables so a host can tune them without
a code change:
    PHISHGUARD_RATE_LIMIT          requests per minute per client (default 30)
    PHISHGUARD_EXPLAIN_LIMIT       explanations per minute per client (default 6)
    PHISHGUARD_EXPLAIN_GLOBAL      explanations per minute, all clients (default 30)
    PHISHGUARD_EXPLAIN_CONCURRENT  explanations running at once (default 2)
    PHISHGUARD_PROXY_HOPS          trusted reverse proxies in front (default 0)
"""

import math
import os
import threading
import time
from collections import OrderedDict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

WINDOW_SECONDS = 60.0
MAX_TRACKED_CLIENTS = 10_000  # bounds memory if many addresses send one request each
SCORING_PATHS = ("/predict", "/explain")
GLOBAL_KEY = "*"

BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}
# The browser UI loads only its own files: no third-party script, style or font.
UI_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
)
# JSON responses never need to load anything.
API_CSP = "default-src 'none'; frame-ancestors 'none'"


def _env_int(name, default):
    """
    Read a positive integer setting from the environment.

    Inputs: name : variable name; default : value when unset.
    Output: the integer value.
    Raises: ValueError naming the variable when it is not a whole number >= 0.
    """
    raw = os.environ.get(name, str(default))
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{name} must be a whole number, got {raw!r}.") from error
    if value < 0:
        raise ValueError(f"{name} must be 0 or more, got {value}.")
    return value


class Settings:
    """
    The security limits in force, read once from the environment.

    Inputs: none (environment variables listed in the module header).
    Output: an object with one attribute per limit.
    """

    def __init__(self):
        self.rate_limit = _env_int("PHISHGUARD_RATE_LIMIT", 30)
        self.explain_limit = _env_int("PHISHGUARD_EXPLAIN_LIMIT", 6)
        self.explain_global = _env_int("PHISHGUARD_EXPLAIN_GLOBAL", 30)
        self.explain_concurrent = max(1, _env_int("PHISHGUARD_EXPLAIN_CONCURRENT", 2))
        self.proxy_hops = _env_int("PHISHGUARD_PROXY_HOPS", 0)


class SlidingWindowLimiter:
    """
    Count requests per key over the last WINDOW_SECONDS seconds.

    Pure apart from the injected clock, so it is testable without sleeping.
    The least recently seen keys are dropped beyond MAX_TRACKED_CLIENTS.

    Inputs: clock : returns the current time in seconds (default monotonic).
    Output: a limiter with allow(key, limit) -> (allowed, retry_after).
    """

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._hits = OrderedDict()
        self._lock = threading.Lock()

    def allow(self, key, limit):
        """
        Record one request for key if it is within limit per window.

        Inputs: key : client address or GLOBAL_KEY; limit : requests per window.
        Output: (allowed, seconds until the oldest counted request expires).
        """
        with self._lock:
            now = self._clock()
            hits = self._hits.setdefault(key, deque())
            self._hits.move_to_end(key)
            while hits and now - hits[0] >= WINDOW_SECONDS:
                hits.popleft()
            if len(hits) >= limit:
                return False, max(1, math.ceil(WINDOW_SECONDS - (now - hits[0])))
            hits.append(now)
            while len(self._hits) > MAX_TRACKED_CLIENTS:
                self._hits.popitem(last=False)
            return True, 0


def client_address(request, proxy_hops):
    """
    Identify the client, trusting only as many proxies as configured.

    Behind N trusted proxies the real client is the Nth address from the right
    of X-Forwarded-For; anything further left was written by the client and
    can be forged, so it is never used.

    Inputs: request : the incoming request; proxy_hops : 0 for direct.
    Output: the client address as a string.
    """
    direct = request.client.host if request.client else "unknown"
    if proxy_hops <= 0:
        return direct
    forwarded = [
        part.strip()
        for part in request.headers.get("x-forwarded-for", "").split(",")
        if part.strip()
    ]
    return forwarded[-proxy_hops] if len(forwarded) >= proxy_hops else direct


def install_security(app: FastAPI, settings=None, limiter=None):
    """
    Add the rate-limit, concurrency and security-header middleware.

    Inputs: app : the FastAPI app; settings : optional Settings (tests);
    limiter : optional SlidingWindowLimiter with a controlled clock (tests).
    Output: the threading.BoundedSemaphore that caps running explanations,
    also stored on app.state.explain_slots.
    """
    settings = settings or Settings()
    limiter = limiter or SlidingWindowLimiter()
    app.state.explain_slots = threading.BoundedSemaphore(settings.explain_concurrent)

    @app.middleware("http")
    async def _guard(request: Request, call_next):
        if request.method == "POST" and request.url.path in SCORING_PATHS:
            refusal = _check_limits(request, settings, limiter)
            if refusal is not None:
                return _with_headers(request, refusal)
        return _with_headers(request, await call_next(request))

    return app.state.explain_slots


def _check_limits(request, settings, limiter):
    """
    Apply the per-client and global limits to one scoring request.

    Inputs: request; settings : Settings; limiter : SlidingWindowLimiter.
    Output: a 429 response if a limit is exceeded, else None.
    """
    client = client_address(request, settings.proxy_hops)
    checks = [(client, settings.rate_limit, "requests from this client")]
    if request.url.path == "/explain":
        checks.append((f"{client}|explain", settings.explain_limit, "explanations from this client"))
        checks.append((GLOBAL_KEY, settings.explain_global, "explanations across all users"))
    for key, limit, what in checks:
        allowed, retry_after = limiter.allow(key, limit)
        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry_after)},
                content={"detail": f"Too many {what}: the limit is {limit} per minute. Try again in {retry_after} s."},
            )
    return None


def _with_headers(request, response):
    """
    Attach the security headers; the UI gets a page CSP, JSON a deny-all one.

    The interactive docs at /docs load their script from a CDN, so they keep
    the base headers only.

    Inputs: request; response.
    Output: the same response, with headers set.
    """
    for name, value in BASE_HEADERS.items():
        response.headers.setdefault(name, value)
    path = request.url.path
    if path.startswith("/ui"):
        response.headers["Content-Security-Policy"] = UI_CSP
    elif not path.startswith(("/docs", "/redoc", "/openapi.json")):
        response.headers["Content-Security-Policy"] = API_CSP
    return response
