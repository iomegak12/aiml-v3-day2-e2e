"""Per-client-IP, in-memory rate limiting with a temporary block.

Rules (all values come from settings):
- A client may send ``limit`` requests per ``window_seconds`` (fixed window that
  starts at the client's first request).
- The request that exceeds the limit starts a ``block_seconds`` block; every
  request during the block gets 429 with Retry-After = remaining seconds.
- After the block, the next request starts a fresh window.

Counters live in this process only: with several workers or replicas each one
counts separately.
"""

import math
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from netcore_tac.api.problems import problem_response, rate_limited_problem

Clock = Callable[[], float]


@dataclass(frozen=True)
class RateLimitDecision:
    """Outcome of one check: allowed or blocked, plus header values."""

    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int
    retry_after: int = 0

    def headers(self) -> dict[str, str]:
        """RateLimit-* headers (and Retry-After when blocked)."""
        headers = {"RateLimit-Limit": str(self.limit),
                   "RateLimit-Remaining": str(self.remaining),
                   "RateLimit-Reset": str(self.reset_seconds)}
        if not self.allowed:
            headers["Retry-After"] = str(self.retry_after)
        return headers


@dataclass
class _ClientState:
    window_start: float | None = None
    count: int = 0
    blocked_until: float = 0.0


class RateLimiter:
    """Thread/async-safe fixed-window limiter with block; inject ``clock`` in tests."""

    def __init__(self, limit: int, window_seconds: float, block_seconds: float,
                 clock: Clock = time.monotonic) -> None:
        if limit < 1 or window_seconds <= 0 or block_seconds <= 0:
            raise ValueError("limit, window_seconds and block_seconds must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self.block_seconds = block_seconds
        self._clock = clock
        self._clients: dict[str, _ClientState] = {}
        self._lock = threading.Lock()
        self._last_cleanup = clock()

    def __len__(self) -> int:
        """Number of tracked clients."""
        return len(self._clients)

    def check(self, key: str) -> RateLimitDecision:
        """Count one request from ``key`` and decide whether it is allowed."""
        with self._lock:
            now = self._clock()
            self._cleanup(now)
            state = self._clients.setdefault(key, _ClientState())

            if state.blocked_until > now:
                return self._blocked(state.blocked_until - now)

            if state.window_start is None or now >= state.window_start + self.window_seconds:
                state.window_start, state.count = now, 0

            if state.count >= self.limit:   # this request exceeds the limit -> block
                state.blocked_until = now + self.block_seconds
                state.window_start, state.count = None, 0
                return self._blocked(self.block_seconds)

            state.count += 1
            reset = math.ceil(state.window_start + self.window_seconds - now)
            return RateLimitDecision(True, self.limit, self.limit - state.count, max(reset, 0))

    def _blocked(self, remaining_block: float) -> RateLimitDecision:
        seconds = max(math.ceil(remaining_block), 1)
        return RateLimitDecision(False, self.limit, 0, seconds, retry_after=seconds)

    def _cleanup(self, now: float) -> None:
        """Drop clients whose window and block have both ended (once per window)."""
        if now - self._last_cleanup < self.window_seconds:
            return
        self._last_cleanup = now
        stale = [key for key, s in self._clients.items()
                 if s.blocked_until <= now
                 and (s.window_start is None or now >= s.window_start + self.window_seconds)]
        for key in stale:
            del self._clients[key]


def client_ip(scope: Scope, trust_proxy_headers: bool) -> str:
    """Client IP: first X-Forwarded-For address if trusted, else the socket peer."""
    if trust_proxy_headers:
        forwarded = Headers(scope=scope).get("x-forwarded-for", "")
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    client = scope.get("client")
    return client[0] if client else "unknown"


class RateLimitMiddleware:
    """Pure ASGI middleware applying a RateLimiter to every non-exempt HTTP path."""

    def __init__(self, app: ASGIApp, limiter: RateLimiter,
                 exempt_paths: Iterable[str] = ("/health", "/ready"),
                 trust_proxy_headers: bool = False) -> None:
        self.app = app
        self.limiter = limiter
        self.exempt_paths = frozenset(exempt_paths)
        self.trust_proxy_headers = trust_proxy_headers

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in self.exempt_paths:
            await self.app(scope, receive, send)
            return

        decision = self.limiter.check(client_ip(scope, self.trust_proxy_headers))
        if not decision.allowed:
            request_id = scope.get("state", {}).get("request_id")
            body = rate_limited_problem(decision.retry_after, scope["path"], request_id)
            await problem_response(body, headers=decision.headers())(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in decision.headers().items():
                    headers[name] = value
            await send(message)

        await self.app(scope, receive, send_with_headers)
