"""
test_security.py
Security headers, the sliding-window rate limiter and client identification.
Author: Colile Sibanda
"""

from types import SimpleNamespace

import pytest

from api.security import (
    WINDOW_SECONDS,
    Settings,
    SlidingWindowLimiter,
    client_address,
)


class FakeClock:
    """A clock the test moves by hand. Output: callable returning the time."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def _request(direct, forwarded=""):
    """Build the two request attributes client_address reads."""
    headers = {"x-forwarded-for": forwarded} if forwarded else {}
    return SimpleNamespace(client=SimpleNamespace(host=direct), headers=headers)


def test_every_response_carries_security_headers(client):
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]


def test_ui_pages_allow_only_their_own_files(client):
    csp = client.get("/ui/").headers["Content-Security-Policy"]
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_limiter_refuses_over_the_limit_and_recovers():
    clock = FakeClock()
    limiter = SlidingWindowLimiter(clock)
    assert all(limiter.allow("a", 3)[0] for _ in range(3))
    allowed, retry_after = limiter.allow("a", 3)
    assert not allowed and retry_after >= 1
    clock.now += WINDOW_SECONDS
    assert limiter.allow("a", 3)[0]


def test_limiter_counts_clients_separately():
    limiter = SlidingWindowLimiter(FakeClock())
    assert limiter.allow("a", 1)[0]
    assert not limiter.allow("a", 1)[0]
    assert limiter.allow("b", 1)[0]


def test_direct_connection_ignores_forwarded_header():
    assert client_address(_request("10.0.0.1", "6.6.6.6"), 0) == "10.0.0.1"


def test_forged_forwarded_entries_are_not_trusted():
    # One trusted proxy appends the real client last; the left entry is forged.
    request = _request("10.0.0.9", "6.6.6.6, 203.0.113.5")
    assert client_address(request, 1) == "203.0.113.5"


def test_invalid_limit_setting_names_the_variable(monkeypatch):
    monkeypatch.setenv("PHISHGUARD_RATE_LIMIT", "many")
    with pytest.raises(ValueError, match="PHISHGUARD_RATE_LIMIT"):
        Settings()
