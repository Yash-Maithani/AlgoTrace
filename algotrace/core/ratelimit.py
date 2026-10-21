"""A per-address rate limit for the endpoints that run an algorithm, standard library only.

/run_floyd_warshall is cubic in the node count and /run_sort takes up to 100 values;
both are cheap to call and not free to answer. This keeps one address from asking
for hundreds of runs a minute, while leaving a student who plays with the controls
well inside the limit (one run is one request, Compare makes two).

  * a sliding window: an address may make `limit` requests in any 60 seconds
  * the address is request.remote_addr. With TRUST_PROXY=1 the app is wrapped in
    werkzeug's ProxyFix first, so that is the client the proxy saw, taken from the
    last X-Forwarded-For entry the one trusted proxy added. Without it a forged
    X-Forwarded-For header is ignored.
  * the counters live in this process. Under gunicorn with two workers each worker
    counts on its own, so the effective limit is up to twice the number set.
  * RATE_LIMIT_PER_MINUTE sets the limit, 30 by default, 0 turns it off.
"""
import math
import os
import threading
import time
from collections import deque

from flask import jsonify, request

DEFAULT_LIMIT = 30
WINDOW_SECONDS = 60
PREFIX = "/run_"
MAX_TRACKED = 10_000        # addresses remembered at once; the idle ones are dropped past this

MESSAGE = ("You are running algorithms faster than this site allows. "
           "Wait %d second%s and try again.")


class Limiter:
    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._seen = {}
        self._lock = threading.Lock()

    def reset(self):
        with self._lock:
            self._seen.clear()

    def check(self, address, limit, window=WINDOW_SECONDS):
        """Count one request from `address`. Returns 0 if it is allowed, or the
        whole seconds to wait until it would be."""
        now = self._clock()
        with self._lock:
            stamps = self._seen.get(address)
            if stamps is None:
                if len(self._seen) >= MAX_TRACKED:
                    self._forget_idle(now, window)
                stamps = self._seen[address] = deque()
            while stamps and now - stamps[0] >= window:
                stamps.popleft()
            if len(stamps) >= limit:
                return max(1, math.ceil(window - (now - stamps[0])))
            stamps.append(now)
            return 0

    def _forget_idle(self, now, window):
        for address in [a for a, s in self._seen.items() if not s or now - s[-1] >= window]:
            del self._seen[address]


def limit_from_environment():
    raw = os.environ.get("RATE_LIMIT_PER_MINUTE", "").strip()
    try:
        return max(0, int(raw)) if raw else DEFAULT_LIMIT
    except ValueError:
        return DEFAULT_LIMIT


def init_rate_limit(app):
    """Refuse the 31st /run_ request an address makes in a minute with a JSON 429.
    The limit is read from app.config on every request, so a test can change it."""
    app.config.setdefault("RATE_LIMIT_PER_MINUTE", limit_from_environment())
    limiter = app.extensions["rate_limiter"] = Limiter()

    @app.before_request
    def limit_runs():
        limit = app.config["RATE_LIMIT_PER_MINUTE"]
        if not limit or request.method != "POST" or not request.path.startswith(PREFIX):
            return None
        wait = limiter.check(request.remote_addr or "unknown", limit)
        if not wait:
            return None
        response = jsonify({"error": MESSAGE % (wait, "" if wait == 1 else "s"), "retry_after": wait})
        response.status_code = 429
        response.headers["Retry-After"] = str(wait)
        return response
