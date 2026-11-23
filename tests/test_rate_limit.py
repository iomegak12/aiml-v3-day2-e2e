"""Unit tests for netcore_tac.api.rate_limit (fake clock, no sleeping)."""

import asyncio
import json

import pytest

from netcore_tac.api.rate_limit import RateLimiter, RateLimitMiddleware, client_ip


class FakeClock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def limiter(clock) -> RateLimiter:
    return RateLimiter(limit=100, window_seconds=60, block_seconds=30, clock=clock)


def send_many(limiter: RateLimiter, n: int, key: str = "1.2.3.4"):
    return [limiter.check(key) for _ in range(n)]


def test_100_allowed_with_remaining_countdown(limiter):
    decisions = send_many(limiter, 100)
    assert all(d.allowed for d in decisions)
    assert [d.remaining for d in decisions[:3]] == [99, 98, 97]
    assert decisions[-1].remaining == 0
    assert decisions[0].headers() == {"RateLimit-Limit": "100", "RateLimit-Remaining": "99",
                                      "RateLimit-Reset": "60"}


def test_101st_blocked_with_retry_after_30(limiter):
    send_many(limiter, 100)
    blocked = limiter.check("1.2.3.4")
    assert not blocked.allowed
    assert blocked.retry_after == 30
    assert blocked.headers()["Retry-After"] == "30"


def test_retry_after_counts_down(limiter, clock):
    send_many(limiter, 101)
    clock.advance(10)
    assert limiter.check("1.2.3.4").retry_after == 20
    clock.advance(19.5)
    assert limiter.check("1.2.3.4").retry_after == 1


def test_unblocked_after_30_seconds(limiter, clock):
    send_many(limiter, 101)
    clock.advance(29.9)
    assert not limiter.check("1.2.3.4").allowed
    clock.advance(0.1)
    decision = limiter.check("1.2.3.4")
    assert decision.allowed and decision.remaining == 99   # fresh window


def test_window_resets_after_60_seconds(limiter, clock):
    send_many(limiter, 100)
    clock.advance(60)
    decision = limiter.check("1.2.3.4")
    assert decision.allowed and decision.remaining == 99


def test_reset_header_counts_down(limiter, clock):
    limiter.check("1.2.3.4")
    clock.advance(45)
    assert limiter.check("1.2.3.4").reset_seconds == 15


def test_clients_counted_separately(limiter):
    send_many(limiter, 101, key="a")
    assert limiter.check("b").allowed


def test_stale_entries_cleaned_up(limiter, clock):
    for i in range(50):
        limiter.check(f"10.0.0.{i}")
    assert len(limiter) == 50
    clock.advance(61)
    limiter.check("new")
    assert len(limiter) == 1


def test_blocked_client_not_cleaned_up_early(clock):
    limiter = RateLimiter(limit=1, window_seconds=10, block_seconds=30, clock=clock)
    send_many(limiter, 2, key="a")   # blocked until +30
    clock.advance(11)
    limiter.check("b")               # triggers cleanup
    assert not limiter.check("a").allowed


def test_invalid_settings_rejected():
    with pytest.raises(ValueError):
        RateLimiter(limit=0, window_seconds=60, block_seconds=30)


def test_client_ip_peer_and_forwarded():
    scope = {"type": "http", "client": ("9.9.9.9", 5000),
             "headers": [(b"x-forwarded-for", b"1.1.1.1, 2.2.2.2")]}
    assert client_ip(scope, trust_proxy_headers=False) == "9.9.9.9"
    assert client_ip(scope, trust_proxy_headers=True) == "1.1.1.1"
    assert client_ip({"type": "http", "client": None, "headers": []}, True) == "unknown"


# --- middleware (called directly as an ASGI app; no server, no TestClient) -------

async def ok_app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"{}"})


def call(middleware, path: str, ip: str = "5.5.5.5"):
    scope = {"type": "http", "method": "GET", "path": path, "headers": [],
             "client": (ip, 1234), "query_string": b"", "state": {"request_id": "rid"}}
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    asyncio.run(middleware(scope, receive, send))
    start = messages[0]
    headers = {k.decode().lower(): v.decode() for k, v in start["headers"]}
    body = b"".join(m.get("body", b"") for m in messages[1:])
    return start["status"], headers, body


@pytest.fixture
def middleware(clock):
    limiter = RateLimiter(limit=2, window_seconds=60, block_seconds=30, clock=clock)
    return RateLimitMiddleware(ok_app, limiter, exempt_paths=("/health", "/ready"))


def test_middleware_adds_ratelimit_headers(middleware):
    status, headers, _ = call(middleware, "/api/v1/predictions")
    assert status == 200
    assert headers["ratelimit-limit"] == "2" and headers["ratelimit-remaining"] == "1"


def test_middleware_returns_429_problem(middleware):
    for _ in range(2):
        call(middleware, "/api/v1/predictions")
    status, headers, body = call(middleware, "/api/v1/predictions")
    assert status == 429
    assert headers["retry-after"] == "30"
    assert headers["content-type"].startswith("application/problem+json")
    problem = json.loads(body)
    assert problem["status"] == 429 and problem["request_id"] == "rid"


def test_probes_exempt(middleware):
    for _ in range(3):
        call(middleware, "/api/v1/predictions")   # now blocked
    for path in ("/health", "/ready"):
        for _ in range(10):
            status, headers, _ = call(middleware, path)
            assert status == 200 and "ratelimit-limit" not in headers
